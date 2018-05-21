import requests
import sys
import os
import json

username = 'hartgx'
password = 'Sillycat12!'
jenkins_url = "10.8.32.114:8080"
build_token = "thynicemouseswing"

temp_master_slavejob_config_file_name = "build_config_tmp.xml"
master_executor_config_file_name = "master_executor_config.xml"
master_slavejob_config_file_name = 'build_config.xml'


master_slavejob_copy_build_name = "SlaveTestBuild"
master_executor_job_name = "BuildAndExecuteRegression"

jenkins_auth_url = 'http://{0}:{1}@{2}'.format(username,password,jenkins_url)

# PATH / URL Creation

def create_sub_dir_path(folder_1,folder_2,folder_3,folder_4):
    work_dir = os.getcwd()
    return work_dir + '\Regression\{0}\{1}\{2}\{3}\\'.format(folder_1, folder_2, folder_3,folder_4)

def create_jenkins_suite_path(folder_1, folder_2, folder_3, folder_4):
    return '/job/{0}/job/{1}/job/{2}/job/{3}'.format(folder_1, folder_2, folder_3, folder_4)

def create_jenkins_folder(name,path):

    folder_create_url_encode = 'name={0}&mode=com.cloudbees.hudson.plugins.folder.Folder&from=&json=%7B%22name%22%3A%22FolderName%22%2C%22mode%22%3A%22com.cloudbees.hudson.plugins.folder.Folder%22%2C%22from%22%3A%22%22%2C%22Submit%22%3A%22OK%22%7D&Submit=OK'.format(name)
    folder_create_url = '{0}/{1}/createItem?{2}'.format(jenkins_auth_url,path,folder_create_url_encode)
    # print(folder_create_url)

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    folder_response = requests.post(folder_create_url,headers=headers)

    if folder_response.status_code != 200:
        print(folder_response.status_code)
        print(folder_response.text)

def get_git_folder_jobs(sub_dir_path):
    uft_test_names = []

    for name in os.listdir(sub_dir_path):
        if os.path.isdir(sub_dir_path+'/'+name):
            uft_test_names.append(name)

    return uft_test_names

def get_jenkins_job_list(suite_path):
    job_list_folder_url = '{0}{1}/api/json'.format(jenkins_auth_url,suite_path)
    # print(job_list_folder_url)

    # Request portion
    job_folder_response = requests.get(job_list_folder_url)

    if job_folder_response.status_code != 200:
        # TODO: Need to figure out logic behind adding all the folders prior to this suite if this suite isn't found
        return None
    else:
        # Parse json response as dictionary
        job_folder_dictionary = json.loads(job_folder_response.text)
        jobs_list = job_folder_dictionary['jobs']

        jobs = []
        for job in jobs_list:
            if job['_class'] == 'hudson.model.FreeStyleProject':
                jobs.append(job['name'])

        return jobs

def check_jenkins_folders(suite_path):
    split_path = suite_path.split('/job/')[1:]

    for i in range(1,len(split_path)):
        if i == 1:
            new_path = "/job/"+split_path[0]
            remainder = split_path[1:]
        else:
            new_path = "/job/"+"/job/".join(split_path[0:i])
            remainder = split_path[i:]
        # print("Jenkins path")
        # print(new_path)

        folder_url = '{0}{1}/api/json'.format(jenkins_auth_url, new_path)
        folder_response = requests.get(folder_url)

        folder_dictionary = json.loads(folder_response.text)
        folder_list = folder_dictionary['jobs']

        folders = []
        for entry in folder_list:
            if entry['_class'] != 'hudson.model.FreeStyleProject':
                folders.append(entry['name'])
        # print("Remainder of path")
        # print(remainder)
        # print("Folders in jenkins url path")
        # print(folders)

        # TODO: Loop on the remaining folders vs the found folders - if one does not exist run folder creation method
        if remainder[0] not in folders:
            create_jenkins_folder(remainder[0],new_path)

### GET CONFIGURATIONS.XMLs FROM JENKINS

def get_master_slavejob_build_configuration():
    config_url = '{0}/job/{1}/config.xml'.format(jenkins_auth_url, master_slavejob_copy_build_name)

    config_response = requests.get(config_url)

    if config_response.status_code != 200:
        print("Grabbing master slave-job build config failed")
        print(config_url)
        print(config_response.status_code)
        print(config_response.text)

    config_file = open(temp_master_slavejob_config_file_name, 'w')
    config_file.write(config_response.text)
    config_file.close()

def get_master_executor_job_configuration():
    config_url = '{0}/job/{1}/config.xml'.format(jenkins_auth_url,master_executor_job_name)

    config_response = requests.get(config_url)

    if config_response.status_code != 200:
        print("Grabbing master executor build config failed")
        print(config_url)
        print(config_response.status_code)
        print(config_response.text)

    config_file = open(master_executor_config_file_name, 'w')
    config_file.write(config_response.text)
    config_file.close()

def get_master_executor_publishers():

    executor_file = open(master_executor_config_file_name,'r')

    grab = False
    publisher_data = []

    for line in executor_file.readlines():
        if '<com.qasymphony.ci.plugin.action.PushingResultAction' in line:
            grab = True
        if '</com.qasymphony.ci.plugin.action.PushingResultAction>' in line:
            grab = False
            publisher_data.append(line)
        if grab:
            publisher_data.append(line)

    executor_file.close()
    return publisher_data

def update_slavejob_configuration(uft_test_suite,test_name,test_path):

    slave_config = open(temp_master_slavejob_config_file_name,'r')
    master_config_publisher = get_master_executor_publishers()
    updated_config = open(master_slavejob_config_file_name,'w')

    slave_data = []
    for line in slave_config.readlines():
        slave_data.append(line)

    paused = False
    skip_write = False
    params = [uft_test_suite,test_name,test_path]
    param_count = 0

    for line in slave_data:

        if 'defaultValue' in line:
            if param_count < 3:
                blank_space = '          '
                new_line = '{0}<defaultValue>{1}</defaultValue>\n'.format(blank_space,params[param_count])
                param_count += 1
                updated_config.write(new_line)
        else:
            if '</com.hpe.application.automation.tools.results.RunResultRecorder>' in line:
                paused = True

            if not paused:
                updated_config.write(line)
            else:
                if not skip_write:
                    for mline in master_config_publisher:
                        updated_config.write(mline)
                    skip_write = True
                    paused=False
                    updated_config.write(line)

    slave_config.close()
    updated_config.close()

### CREATING AND UPDATING JOBS

def create_new_jenkins_job(job_name,jenkins_suite_path):
    data = open(master_slavejob_config_file_name, 'rb').read()

    job_creation_url = '{0}{1}/createItem?name={2}'.format(jenkins_auth_url,jenkins_suite_path,job_name)

    headers = {
        'Content-Type': 'text/xml',
    }

    response = requests.post(job_creation_url, headers=headers, data=data)

    if response.status_code != 200:
        print("Creating jenkins job failed")
        print(job_creation_url)
        print(response.status_code)
        print(response.text)

def update_jenkins_job(job_name,jenkins_suite_path):
    data = open(master_slavejob_config_file_name, 'rb').read()
    job_update_url = '{0}{1}/job/{2}/config.xml'.format(jenkins_auth_url,jenkins_suite_path,job_name)

    headers = {
        'Content-Type': 'text/xml',
    }

    response = requests.post(job_update_url, headers=headers, data=data)
    if response.status_code != 200:
        print("Updating jenkins job failed")
        print(job_update_url)
        print(response.status_code)
        print(response.text)

def run_jenkins_job_build(job_path,test_name,test_path,test_suite):
    print(job_path)
    print(test_name)
    print(test_suite)

    params = (
        ('token', build_token),
        ('TEST_NAME', test_name),
        ('TEST_PATH', test_path),
        ('TEST_SUITE', test_suite),
    )

    post_url = 'http://{0}:{1}@{2}{3}/job/{4}/buildWithParameters'.format(username,password,jenkins_url,job_path,test_name)
    print ("Post URL")
    print (post_url)
    response = requests.post(post_url, params=params)
    print (params)
    print (response)

def main(suite_path,uft_suite_name):

    split_suite = suite_path.split('/')

    # Create the folder path for that suite
    path = create_sub_dir_path(split_suite[0], split_suite[1], split_suite[2], split_suite[3])

    # Get a list of all the tests in the suite folder
    tests_to_run = get_git_folder_jobs(path)

    # Create the jenkins url path for the specified suite to check if it exists
    jenkins_suite_path = create_jenkins_suite_path(split_suite[0], split_suite[1], split_suite[2], split_suite[3])

    # Get list of jobs for that suite
    jenkins_job_list = get_jenkins_job_list(jenkins_suite_path)

    # If jenkins_job_list is returned as None we know that suite doesnt exist in jenkins
    # Check all it's sub paths and create the folders where nessecary
    if jenkins_job_list is None:
        check_jenkins_folders(jenkins_suite_path)

    # Grab and save a copy of the master slave build config.xml for use in creating/updating jobs
    get_master_slavejob_build_configuration()
    get_master_executor_job_configuration()


    for job in tests_to_run:
        uft_test_path = path +'\\'+job
        test_path = uft_test_path.replace('BuildAndExecuteRegression', job)
        update_slavejob_configuration(uft_suite_name,job,test_path)

        # If name of git repo UFT test is not in jenkins as a job name - create a new job for it
        # based on the config.xml of our MASTER slave build
        if jenkins_job_list is not None:
            if job not in jenkins_job_list:
                create_new_jenkins_job(job, jenkins_suite_path)


            # If name of git repo test is in jenkins as a job name - by default update the test to use the current
            # config.xml from the MASTER slave build
            else:
                update_jenkins_job(job,jenkins_suite_path)
        # In the case we had no jobs in the jenkins list to compare to, build all the jobs
        else:
            create_new_jenkins_job(job, jenkins_suite_path)

    # For all the jobs in the suite we just updated or build - call their build on jenkins so they run
    for job in tests_to_run:
        uft_test_path = path +'\\'+job
        test_path = uft_test_path.replace('BuildAndExecuteRegression', job)
        print ("Executing test")
        print ("Build info %s | %s | %s | %s" % (jenkins_suite_path,job,test_path,uft_suite_name))
        run_jenkins_job_build(jenkins_suite_path,job,test_path,uft_suite_name)
        print ("Executed test")

if __name__ == "__main__":
    suite_path = sys.argv[1]
    uft_suite_name = sys.argv[2]
    main(suite_path,uft_suite_name)