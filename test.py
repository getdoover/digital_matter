import uuid
import os
import base64
import sys
import zipfile
import importlib.util
import shutil


def main():
    processor_package_dir = "processor"
    shutil.make_archive("temp_processor_package", 'zip', processor_package_dir)
    with open("temp_processor_package.zip", "rb") as f:
        zip_bytes = f.read()

    b64_package = base64.b64encode(zip_bytes).decode()

    package_kwargs = dict(
        agent_id="9fb5d629-ce7f-4b08-b17a-c267cbcd0427",
        access_token="e9c92fe2996390ca7ebded4af918cde701d87ac7",
        api_endpoint="https://my.d.doover.dev",
        package_config={},
        msg_obj={},
        task_id="d1c7e8e3-f47b-4c68-86d7-65054d9e97d3",
        log_channel="1f71b8bd-9444-4f34-859f-f339875a765c",
        agent_settings={
            "deployment_config": {}
        }
    )
    #### Setup the environment

    invocation_id = str(uuid.uuid4())
    package_kwargs['sandbox_invocation_id'] = invocation_id

    tmp_folder = "/tmp/doover_code_sandbox/" + invocation_id + "/"
    if not os.path.exists(tmp_folder):
        os.makedirs(tmp_folder)

    orig_cwd = os.getcwd()
    os.chdir(tmp_folder)

    ## Setup the package

    zipfile_name = 'target.zip'
    zipfile_name = os.path.join(os.path.dirname(tmp_folder), zipfile_name)
    with open(zipfile_name, 'wb') as result:
        result.write(base64.b64decode(b64_package))

    with zipfile.ZipFile(zipfile_name, 'r') as zip_ref:
        zip_ref.extractall('./')

    ## add the current directory to the path
    # if 'sandbox_version' == 1:
    sys.path.append(tmp_folder)

    # package_kwargs['sys_path'] = sys.path
    # package_kwargs['python_modules'] = sys.modules

    # Path( os.path.join(tmp_folder, '__init__.py') ).touch()

    ## import the loaded generator file
    spec = importlib.util.spec_from_file_location("target", "target.py")
    target_task = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(target_task)

    # from .target import generator
    target_task = getattr(target_task, 'target')

    # task_obj = target_task(
    #     doover_endpoint=doover_endpoint,
    #     agent_id=agent_id,
    #     access_token=access_token,
    #     task_config=task_config,
    #     msg_log=msg_log,
    # )
    task_obj = target_task(
        **package_kwargs
    )

    task_obj.execute()

    #### Clean up environment

    sys.path.remove(tmp_folder)
    os.chdir(orig_cwd)
    shutil.rmtree(tmp_folder)


if __name__ == '__main__':
    main()
