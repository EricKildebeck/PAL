# sample2_pools_and_resourcefiles.py Code Sample
#
# Copyright (c) Microsoft Corporation
#
# All rights reserved.
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from __future__ import print_function
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import datetime
import os

import azure.storage.blob as azureblob
import azure.batch._batch_service_client as batch
import azure.batch.batch_auth as batchauth
import azure.batch.models as batchmodels

import PolycraftAIGym.common.helpers as helpers

_CONTAINER_NAME = 'batch-workflow-test'
# APPLICATION_ID = 'image-test'
APPLICATION_ID = 'agent_sift'
APPLICATION_VERSION = '1'
# APPLICATION_ID_FIXED = 'image_test'
APPLICATION_ID_FIXED = 'agent_sift'
APPLICATION_DIR = '$AZ_BATCH_APP_PACKAGE_' + APPLICATION_ID_FIXED + '_' + APPLICATION_VERSION
# POOL_ID = "ImageTestPool"
POOL_ID = "FogWar25_01"
# _SIMPLE_TASK_NAME = 'simple_task.py'
# _SIMPLE_TASK_PATH = os.path.join('resources', 'simple_task.py')


def create_pool(batch_client, block_blob_client, pool_id, vm_size, vm_count):
    """Creates an Azure Batch pool with the specified id.

    :param batch_client: The batch client to use.
    :type batch_client: `batchserviceclient.BatchServiceClient`
    :param block_blob_client: The storage block blob client to use.
    :type block_blob_client: `azure.storage.blob.BlockBlobService`
    :param str pool_id: The id of the pool to create.
    :param str vm_size: vm size (sku)
    :param int vm_count: number of vms to allocate
    """
    # pick the latest supported 16.04 sku for UbuntuServer
    sku_to_use, image_ref_to_use = \
        helpers.select_latest_verified_vm_image_with_node_agent_sku(
            batch_client, 'Canonical', 'UbuntuServer', '18.04')

    block_blob_client.create_container(
        _CONTAINER_NAME,
        fail_on_exist=False)

    # sas_url = helpers.upload_blob_and_create_sas(
    #     block_blob_client,
    #     _CONTAINER_NAME,
    #     _SIMPLE_TASK_NAME,
    #     _SIMPLE_TASK_PATH,
    #     datetime.datetime.utcnow() + datetime.timedelta(hours=1))

    application_package_references = [
        batchmodels.ApplicationPackageReference(application_id=APPLICATION_ID, version=APPLICATION_VERSION),
    ]
    # pool = batchmodels.PoolAddParameter(
    #     id=pool_id,
    #     virtual_machine_configuration=batchmodels.VirtualMachineConfiguration(
    #         image_reference=image_ref_to_use,
    #         node_agent_sku_id=sku_to_use),
    #     vm_size=vm_size,
    #     target_dedicated_nodes=vm_count,
    #     application_package_references=application_package_references,
    #     start_task=batchmodels.StartTask(
    #         command_line="python --version"))

    pool = batch.models.PoolAddParameter(
        id=pool_id,
        virtual_machine_configuration=batchmodels.VirtualMachineConfiguration(
            image_reference=batchmodels.ImageReference(
                publisher="Canonical",
                offer="UbuntuServer",
                sku="18.04-LTS",
                version="latest"
            ),
            node_agent_sku_id="batch.node.ubuntu 18.04"),
        vm_size=vm_size,
        target_dedicated_nodes=vm_count,
        application_package_references=application_package_references,
        start_task=batchmodels.StartTask(
            command_line=helpers.wrap_commands_in_shell('linux', [
                'apt-get install software-properties-common',
                'apt-add-repository universe',
                'apt-get update',
                'sudo apt-get install -y python3-pip'
                ]),
            wait_for_success=True,
            user_identity=batchmodels.UserIdentity(
                auto_user=batchmodels.AutoUserSpecification(
                    scope=batchmodels.AutoUserScope.pool,
                    elevation_level=batchmodels.ElevationLevel.admin)),
        ))

    helpers.create_pool_if_not_exist(batch_client, pool)


def submit_job_and_add_task(batch_client, block_blob_client, job_id, pool_id):
    """Submits a job to the Azure Batch service and adds
    a task that runs a python script.

    :param batch_client: The batch client to use.
    :type batch_client: `batchserviceclient.BatchServiceClient`
    :param block_blob_client: The storage block blob client to use.
    :type block_blob_client: `azure.storage.blob.BlockBlobService`
    :param str job_id: The id of the job to create.
    :param str pool_id: The id of the pool to use.
    """
    job = batchmodels.JobAddParameter(
        id=job_id,
        pool_info=batchmodels.PoolInformation(pool_id=pool_id))

    batch_client.job.add(job)

    block_blob_client.create_container(
        _CONTAINER_NAME,
        fail_on_exist=False)

    #os.chdir('../output/')
    count = 0
    for file in os.listdir(os.getcwd() + '../fog_of_war'):
        if not file.endswith(".zip"):
            continue
        filename = file.split('.')[0]

        application_package_references = [
            batchmodels.ApplicationPackageReference(application_id=APPLICATION_ID, version=APPLICATION_VERSION),
        ]

        user_identity = batch.models.UserIdentity(auto_user=batch.models.AutoUserSpecification(
                scope=batch.models.AutoUserScope.pool,
                elevation_level=batch.models.ElevationLevel.admin))

        sas_url = helpers.upload_blob_and_create_sas(
            block_blob_client,
            _CONTAINER_NAME,
            'inputs-test/' + file,
            '../fog_of_war' + file,
            datetime.datetime.utcnow() + datetime.timedelta(hours=1))

        setup_url = helpers.upload_blob_and_create_sas(
            block_blob_client,
            _CONTAINER_NAME,
            "setup_azure_vm.sh",
            'setup_azure_vm.sh',
            datetime.datetime.utcnow() + datetime.timedelta(hours=1))

        ## setup
        ## polycraft
            ## pal
                ## agents
                ## {file}
                ##

        task = batchmodels.TaskAddParameter(
            id="MyPythonTask-" + str(count),
            command_line=helpers.wrap_commands_in_shell('linux', [
                './setup/setup_azure_vm.sh',
                f'unzip {file} && mv {file}/ polycraft/pal/'
                'cd polycraft/pal',
                'mkdir agents/',
                'mv ' + APPLICATION_DIR + '/* ./agents/',
                './agents/SIFT_SVN/code/docker/build.sh',
                f'python polycraft/pal/PolycraftAIGym/LaunchTournament.py -t "{filename}" -g "../{file}"'
                # 'printenv',
                # 'sudo -S apt-get install -y python3-opencv',
                # 'sudo pip3 install -r ' + APPLICATION_DIR + '/requirements.txt',
                # 'python3 ' + APPLICATION_DIR + '/sense_screen_image.py'
                ]),
            resource_files=[
                            batchmodels.ResourceFile(
                                file_path= file,
                                http_url=sas_url),
                            batchmodels.ResourceFile(
                                file_path='setup/' + 'setup_azure_vm.sh',
                                http_url=setup_url),
                           ],
            application_package_references=application_package_references,
            user_identity=user_identity)

        batch_client.task.add(job_id=job.id, task=task)

        count += 1


def execute_sample(global_config, sample_config):
    """Executes the sample with the specified configurations.

    :param global_config: The global configuration to use.
    :type global_config: `configparser.ConfigParser`
    :param sample_config: The sample specific configuration to use.
    :type sample_config: `configparser.ConfigParser`
    """
    # Set up the configuration
    batch_account_key = global_config.get('Batch', 'batchaccountkey')
    batch_account_name = global_config.get('Batch', 'batchaccountname')
    batch_service_url = global_config.get('Batch', 'batchserviceurl')

    storage_account_key = global_config.get('Storage', 'storageaccountkey')
    storage_account_name = global_config.get('Storage', 'storageaccountname')
    storage_account_suffix = global_config.get(
        'Storage',
        'storageaccountsuffix')
    storage_account_connection_string = global_config.get('Storage', 'storageconnectionstring')

    should_delete_container = sample_config.getboolean(
        'DEFAULT',
        'shoulddeletecontainer')
    should_delete_job = sample_config.getboolean(
        'DEFAULT',
        'shoulddeletejob')
    should_delete_pool = sample_config.getboolean(
        'DEFAULT',
        'shoulddeletepool')
    pool_vm_size = sample_config.get(
        'DEFAULT',
        'poolvmsize')
    pool_vm_count = sample_config.getint(
        'DEFAULT',
        'poolvmcount')

    # Print the settings we are running with
    helpers.print_configuration(global_config)
    helpers.print_configuration(sample_config)

    credentials = batchauth.SharedKeyCredentials(
        batch_account_name,
        batch_account_key)
    batch_client = batch.BatchServiceClient(
        credentials,
        batch_url=batch_service_url)

    # Retry 5 times -- default is 3
    batch_client.config.retry_policy.retries = 5

    block_blob_client = azureblob.BlockBlobService(
        account_name=storage_account_name,
        account_key=storage_account_key,
        endpoint_suffix=storage_account_suffix)
    # https://pal.centralus.batch.azure.com

    # block_blob_client = azureblob.BlobServiceClient.from_connection_string(
    #     storage_account_connection_string)

    job_id = helpers.generate_unique_resource_name(
        "ImageTestJob")
    pool_id = POOL_ID
    try:
        create_pool(
            batch_client,
            block_blob_client,
            pool_id,
            pool_vm_size,
            pool_vm_count)

        submit_job_and_add_task(
            batch_client,
            block_blob_client,
            job_id, pool_id)

        helpers.wait_for_tasks_to_complete(
            batch_client,
            job_id,
            datetime.timedelta(minutes=25))

        tasks = batch_client.task.list(job_id)
        task_ids = [task.id for task in tasks]

        # helpers.print_task_output(batch_client, job_id, task_ids)
    finally:
        # clean up
        if should_delete_container:
            block_blob_client.delete_container(
                _CONTAINER_NAME,
                fail_not_exist=False)
        if should_delete_job:
            print("Deleting job: ", job_id)
            batch_client.job.delete(job_id)
        if should_delete_pool:
            print("Deleting pool: ", pool_id)
            batch_client.pool.delete(pool_id)


if __name__ == '__main__':
    global_config = configparser.ConfigParser()
    global_config.read(helpers._SAMPLES_CONFIG_FILE_NAME)

    sample_config = configparser.ConfigParser()
    # sample_config.read(
    #     os.path.splitext(os.path.basename(__file__))[0] + '.cfg')
    sample_config.read(helpers._SAMPLES_CONFIG_FILE_NAME)

    execute_sample(global_config, sample_config)