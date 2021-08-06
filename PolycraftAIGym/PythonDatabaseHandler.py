from PolycraftAIGym.AzureConnectionService import AzureConnectionService
from PolycraftAIGym.PalMessenger import PalMessenger
from PolycraftAIGym.AMOCCalculations import AMOC_Calculations
import pandas as pd
import numpy as np
from enum import Enum


class AnalyticMode(Enum):
    UPDATE_ZONES = "update performance zone lookup table. Required args: 'csv_file'"
    UPLOAD_CSV = "insert arbitrary CSV file into a pre-existing table. Columns must match table exactly! Required Args: 'csv_file', 'tbl_name' "
    WILCOXON = "perform wilcoxon rank-sum test on a specific agent and tournament launch date. Required Args: 'agent_name', 'launch_date', 'output_file_name'"
    AMOC = "run the AMOC curve analysis, as defined by Mayank. Required Args: 'agent_name', 'tournament_likeness'."


class PythonDatabaseHandler:
    def __init__(self, mode, debug=False, **kwargs):
        self.pm = PalMessenger(True, False)
        self.azure = AzureConnectionService(self.pm)
        self.debug = debug

        if mode == AnalyticMode.UPDATE_ZONES:
            """
            This code updates the LOOKUP_PERFORMANCE_ZONES table using a CSV generated by the 
            ActiveNoveltyTestingResults.xlsx available in SharePoint (see columns AA-AH on the Lookup Zones sheet)
            Please visit that sheet to get instructions on how to format the input file. 
            """
            if 'csv_file' in kwargs:
                # Do something
                self.upload_to_sql(csv_file=kwargs['csv_file'])
            else:
                print(f"Error! Incorrect Arguments Passed. Mode requires:\n {mode.value}")

        if mode == AnalyticMode.UPLOAD_CSV:
            """
            This code uploads a given CSV into a given Table in SQL. Note that both arguments must be 
            present for this to execute and the CSV File format must exactly match that of the table where you want 
            to insert values. 
            Currently, the python check only confirms that the number of columns match. You will receive a 
            SQL exception if the data types you attempt to upload do not match up (i.e., column order is mixed up) 
            """
            if 'csv_file' in kwargs and 'tbl_name' in kwargs:
                # Do something
                self.upload_to_sql(csv_file=kwargs['csv_file'], tbl_name=kwargs['tbl_name'])
            else:
                print(f"Error! Incorrect Arguments Passed. Mode requires:\n {mode.value}")

        if mode == AnalyticMode.AMOC:
            """
            This code runs the AMOC analysis as designed by Mayank at ISI and requires an agent_name and tournament launch date
            The code automatically pulls the relevant data from SQL. You can pass a specific tournament type 
            (i.e. "POGO_L01_T01_S01") instead of a launch date, if you prefer. The variable is named 
            "tournament_likeness" for this reason.
            Please see @link(AMOCCalculations.AMOC_Calculations) for more details and the exact SQL query. 
            """
            if 'title' in kwargs:
                self.do_amoc_calculation(**kwargs)
            else:
                print(f"Error! Incorrect Arguments Passed. Mode requires:\n {mode.value}")

        if mode == AnalyticMode.WILCOXON:
            """
            This code performs the Wilcoxon Rank Sum Test on a given Agent's set of Tournaments, 
            comparing performance to the agent's VIRGIN tournament defined the wilcoxon_analysis() function
            
            The agent's virgin tournament scores are adjusted by the average shift between pre-novelty and novelty
            performance zones for the particular type and difficulty of novelty being ranked against.
            
            Results are saved to a CSV file (one row per tournament to perform the analysis for.
            """
            if 'agent_name' in kwargs and 'launch_date' in kwargs and 'output_file_name' in kwargs:
                self.wilcoxon_analysis(agent_name=kwargs['agent_name'], launch_date=kwargs['launch_date'], output_file_name=kwargs['output_file_name'])
            else:
                print(f"Error! Incorrect Arguments Passed. Mode requires:\n {mode.value}")

    def wilcoxon_analysis(self, agent_name, launch_date, output_file_name):
        """
        Calculates the Wilcoxon Rank Sum Scores for a set of tournaments run by a defined agent on a tournament launch date
        :param agent_name: Nameo of Agent to perform the Test on
        :param launch_date: Set of Novelty Tournaments to calculate Data. (this is can also be
        :param output_file_name: Name of Output CSV to save results into
        :return:
        """

        # Update this dict as necessary
        virgin_tournament_dict = {
            'SIFT_AGENT_TEST_V6': 'POGO_L00_T01_S01_VIRGIN_X0100_A_U9999_V0_062611',
            'TUFTS_AGENT_TEST_V3': 'POGO_L00_T01_S01_VIRGIN_X0100_A_U9999_V0_062322',
        }
        if agent_name not in virgin_tournament_dict:
            print(f"Error: Virgin Tournament for comparison not provided. Please update VIRGIN_TOURNAMENT_DICT in wilcoxon_analysis()")
            return

        # Get the Baseline Tournament Data
        baselineA = self._get_data_from_sql(agent_name, virgin_tournament_dict[agent_name])
        # i.e. baselineA = get_data_from_sql("TUFTS_AGENT_TEST_V3", 'POGO_L00_T01_S01_VIRGIN_X0100_A_U9999_V0_062322')

        # Add VIRGIN identifier
        baselineA.insert(0, 'type', 'VIRGIN')

        # Drop column with duplicate name - it causes issues. Moreover, this calculation is performed per Agent.
        baselineA = baselineA.drop("Agent_Name", axis=1)

        # get all other data for an agent & a launch date:
        df = self._get_data_from_sql(agent_name, launch_date)
        # e.g. df = get_data_from_sql("TUFTS_AGENT_TEST_V3", "062622")

        # Ignore Virgin Tournaments in the second pull, just in case
        remainder = df[~df['Tournament_Name'].str.contains('VIRGIN')]

        # Drop column with duplicate name - it causes issues. Moreover, this calculation is performed per Agent.
        remainder = remainder.drop("Agent_Name", axis=1)

        # For each group, UNION ALL the baseline data and calculate the wilcoxon rank
        answers = remainder.groupby('Tournament_Name').apply(lambda grp: self._adjust_score_rank_games(grp, baselineA))
        # answers.to_csv("TUFTS_Pre_Novelty_Base_070722_Dense.csv")
        answers.to_csv(f"{output_file_name}.csv")
        print(answers)

    def _get_data_from_sql(self, agent_name, tournament_likeness):
        # a = f"SELECT * FROM {agent_name}_Results_View where Tournament_Name like '%{tournament_likeness}%'"
        if self.debug:
            a = f"SELECT TOP (10000) A.*, ZONE.* FROM {agent_name}_Results_View A LEFT JOIN LOOKUP_PERFORMANCE_ZONES ZONE on Zone.Agent_Name = '{agent_name}' and A.Tournament_Name like '%' + Zone.Tournament_Name + '%' where A.Tournament_Name like '%{tournament_likeness}%'"
        else:
            a = f"SELECT A.*, ZONE.* FROM {agent_name}_Results_View A LEFT JOIN LOOKUP_PERFORMANCE_ZONES ZONE on Zone.Agent_Name = '{agent_name}' and A.Tournament_Name like '%' + Zone.Tournament_Name + '%' where A.Tournament_Name like '%{tournament_likeness}%'"

        # pm = PalMessenger(True, False)
        # azure = AzureConnectionService(pm)
        if self.azure.is_connected():
            return pd.read_sql(a, self.azure.sql_connection)

    def _adjust_score_rank_games(self, group, baselineA):
        """
        Stacks the Virgin tournament data on top of the group (agent & specific tournament in database)
        Adjusts the Virgin tournament scores based on a adjustment formula:
            shift baseline final reward score by avg. of novelty performance zone and the corresponding difficulty performance zone for
            the matching game ID novelty tournament where novelty with some level of difficulty exists.
            That way, the expectation is that if Novelty is successfully utilized, the novelty tournament should have a score improvement compared to our shifted baseline score.

        :param group: Novelty Tournament Data (result of PD.Groupby using agent name and tournament name)
        :param baselineA: Virgin tournament Data
        :return: DataFrame that contains a single row of results for each novelty tournament passed into this function.
        """

       # get list of columns to reduce the result into
        original_cols = baselineA.columns.to_list()

        #LEFT JOIN the two datasets to adjust the scores of the GROUP by the performance zones, defined in BaselineA
        merged_baseline = baselineA.merge(group, on='Game_ID', how='outer', suffixes=('', '_other'))
        # merged_baseline = baselineA.join(group, on='Game_ID', how='left', rsuffix='_other')

        # Adjust Virgin Values
        new_cols = merged_baseline.columns.to_list()
        if 'Difficulty_other' not in new_cols:
            print("Error! Difficulty_other not in the list!")

        #save the old values into a new column, Final_Reward_Old
        merged_baseline['Final_Reward_Old'] = merged_baseline['Final_Reward']

        # Adjust Virgin Baseline scores
        # Shift them by difference of average PreNovelty Performance zone and Difficulty-Specific performance zone
        # Note: use the difficulty of the game with the same GameID in the GROUP dataset, as all virgin tournaments have difficulty = Null
        merged_baseline['Final_Reward'] = merged_baseline.apply(lambda d:
            d['Final_Reward_Old'] if (pd.isnull(d['Difficulty_other']) or pd.isnull(d['PreNovelty_Low_other']))
            else (
                d['Final_Reward_Old'] -
                    (
                        (d['PreNovelty_High_other'] + d['PreNovelty_Low_other']) / 2.0 -
                        (d['Easy_High_other'] + d['Easy_Low_other']) / 2.0
                    )
                if d['Difficulty_other'] == "Easy" else (
                    d['Final_Reward_Old'] -
                        (
                            (d['PreNovelty_High_other'] +d['PreNovelty_Low_other']) / 2.0 -
                            (d['Medium_High_other'] + d['Medium_Low_other']) / 2.0
                        )
                    if d['Difficulty_other'] == "Medium" else (
                        d['Final_Reward_Old'] -
                        (
                            (d['PreNovelty_High_other'] + d['PreNovelty_Low_other']) / 2.0 -
                            (d['Hard_High_other'] + d['Hard_Low_other']) / 2.0
                        )
                        if d['Difficulty_other'] == "Hard" else (
                            d['Final_Reward_Old'])
                    )
                )
            ), axis=1)

        # remove extraneous columns (suffixed by _other), as they are no longer needed
        merged_baseline = merged_baseline[original_cols]

        # add the "NOVEL" type column (it was already added as "VIRGIN" for baseline)
        group.insert(0, 'type', 'NOVEL')

        # UNION ALL THE VIRGIN Data with the NOVEL data
        r = pd.concat([group, merged_baseline])
        # Take the max of intermediate reward and Final Reward as the "Score" to rank for both distributions
        r['Adjusted_Reward'] = r[['Final_Reward', 'Intermediate_Reward']].values.max(1)

        #Perform the ranking - if the scores are identical, assign matching scores the average rank.
        r['rank'] = r['Adjusted_Reward'].rank(method='average')

        # Sum ranks of the baseline tournament (where type == VIRGIN)
        r['r_sum_base'] = r.apply(lambda f: (f['rank']) * np.where(f['type'] == 'VIRGIN', 1, 0), axis=1)
        # Sum ranks of the novelty tournament (where type == NOVEL)
        r['r_sum_novel'] = r.apply(lambda f: (f['rank']) * np.where(f['type'] == 'NOVEL', 1, 0), axis=1)
        # r['Avg_Adjusted'] = r.apply(avg, axis=1)
        grouped = r.groupby('Tournament_Name')

        # Perform the necessary wilcoxon calculations for the novelty and baseline tournaments (sum of ranks, count of instances)
        e = grouped.apply(lambda x: pd.Series(dict(
            avg_base_adjusted_reward=x[x['type'] == 'VIRGIN']['Adjusted_Reward'].sum(),  # helps calc. avg for comparison
            avg_novel_adjusted_reward=x[x['type'] == 'NOVEL']['Adjusted_Reward'].sum(),  # helps calc. avg for comparison
            # avg_final_reward=x.Adjusted_Reward.sum(),
            R=x['rank'].sum(),  # get sum of ranks for each tournament type
            N=x['rank'].count(),  # get count of games for each tournament type
        )))
        total = e['N'].product()

        # We want one row per novelty tournament in the outputs, so we need to flatten the above into a single row
        result = pd.DataFrame()

        # Create the ID column for this "flattened" result - the name of the Novelty Tournament
        result.insert(0, 'Tournament_Name', [i for i in e.index if 'VIRGIN' not in i])

        # Create Result Dataframe of values for this flattened result
        for index, row in e.iterrows():
            if 'VIRGIN' in index:
                result.insert(1, 'V_R1', [row['R']]) # Sum of Ranks for Virgin Tournament
                result.insert(2, 'V_N1', [row['N']]) # Count of Games in Virgin Tournament
                result.insert(3, 'V_U1', [(row['R'] - (row['N'] * (row['N'] + 1)) / 2)]) # Wilcoxon U-Value of Virgin Tournament
                result.insert(4, 'Avg_Baseline_Reward', [(row['avg_base_adjusted_reward']) / row['N']]) # Avg. Adjusted Reward of Virgin (for comparisons)
                continue

            result.insert(5, 'R1', [row['R']]) # Sum of Ranks for Novelty Tournament (of Group)
            result.insert(6, 'N1', [row['N']]) # Count of Games in Novelty Tournament (of Group)
            result.insert(7, 'U1', [(row['R'] - (row['N'] * (row['N'] + 1)) / 2)]) # Wilcoxon U-Value of Novelty TOurnament
            result.insert(8, 'Avg_Novel_Reward', [(row['avg_novel_adjusted_reward']) / row['N']]) # Avg. Adjust Reward of Novelty Tournament Games

        # Normalize U-Values by product of game counts (U value divided by (N1 * V_N1))
        result.insert(9, 'V_U_Normalized', [float(result['V_U1'] / total)])
        result.insert(10, 'U_Normalized', [float(result['U1'] / total)])

        return result


    def do_amoc_calculation(self, **kwargs):
        amc = AMOC_Calculations(title=kwargs['title'], **kwargs)
        amc.calculate()
        amc.create_amoc_plots()

    def upload_to_sql(self, csv_file, tbl_name='LOOKUP_PERFORMANCE_ZONES'):
        df = pd.read_csv(csv_file)
        rows_to_add = []
        for index, row in df.iterrows():
            rows_to_add.append(row.to_dict())

        uploads = []
        for dict in rows_to_add:
            uploads.extend([tuple(dict.values())])

        # pm = PalMessenger(True, False)
        # azure = AzureConnectionService(pm)
        if self.azure.is_connected():
            cursor = self.azure.sql_connection.cursor()
            # replace rows where this agent & tournament exist
            a = df.groupby(['TOURNAMENT_NAME', 'Agent_Name'])
            for name, groups in a:
                cursor.execute(f"""
                    SELECT *
                    FROM {tbl_name}
                    WHERE TOURNAMENT_NAME = '{name[0]}' and Agent_Name = '{name[1]}'
                """)
                if cursor.fetchone() is not None:
                    print(
                        f"Deleting entries from {tbl_name}: TOURNAMENT_NAME = '{name[0]}' and Agent_Name = '{name[1]}'")
                    cursor.execute(f"""
                        DELETE FROM {tbl_name}
                        WHERE TOURNAMENT_NAME = '{name[0]}' and Agent_Name = '{name[1]}'
                    """)
                    self.azure.sql_connection.commit()
                else:
                    continue

            r = f"""INSERT INTO {tbl_name} 
                    ({', '.join([i for i in rows_to_add[0].keys()])}) 
                    VALUES ({', '.join(['?' for i in uploads[0]])}) 
                ;"""

            cursor.executemany(r, uploads)
            self.azure.sql_connection.commit()