from contextvars import ContextVar

import socketio
from devchat.workflow.workflow import Workflow
import asyncio

import time

# sio_app = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*", logger=True)

WorkflowProcCTXVar = ContextVar("WorkflowProc", default=None)
workflow_process = {} # global dict to store workflow p

class workflowProcCommunicator(socketio.AsyncServer):
    proc_in_handler = None



sio_app = workflowProcCommunicator(async_mode="asgi", cors_allowed_origins="*", logger=True)


@sio_app.event
async def connect(sid, environ):
    print(f"new client connected to this id: {sid}, \nenviron: {environ}")


@sio_app.event
async def disconnect(sid):
    print(f"client disconnected from this id: {sid}")


@sio_app.event
async def chat_message(sid, data):
    print(f"message:\n{data}")
    res = "some message blabla"
    await sio_app.emit("reply", res)

@sio_app.event
async def workflow_process_input(sid, data):
    print(f"\n-- workflow_process_input:\n{data}")
    wf_proc = workflow_process.get("wf_proc")
    if wf_proc is not None:
        wf_proc.stdin.write(data)
        wf_proc.stdin.flush()


@sio_app.event
async def start_workflow(sid, data):
    print(f"\n- start workflow data:\n{data}")

    res = f"some workflow start blabla. data: {data}"
    await sio_app.emit("reply", res)
    workflow_name = data["workflow_name"]
    workflow_input = data["workflow_input"]

    workflow = Workflow.load(workflow_name)
    assert workflow, f"workflow {workflow_name} not found"

    workflow._sio_TMP = sio_app
    workflow._wf_proc_ctx_var = WorkflowProcCTXVar
    workflow._wf_processes = workflow_process
    
    workflow.setup(
        model_name=None, # TODO;
        user_input=workflow_input,
        history_messages=None, # TODO:
        parent_hash=None, # TODO:
    )
    return_code = await workflow.a_run_steps()

    # res = f"workflow {workflow_name} finished with return code: {return_code}"
    # # print("### sleep 5 seconds before emit workflow_finish")
    # # time.sleep(5)
    # WorkflowProcCTXVar.set(None)
    # await sio_app.emit("workflow_finish", res)

# TODO: session? room?
async def send_workflow_output(output):
    await sio_app.emit("workflow_output", output)



processes = {}

import subprocess
import os
from pathlib import Path

script_dir = Path(__file__).parent.parent / "script"



@sio_app.event
async def start_process(sid, data):
    # script_file = script_dir / "repeat.py"
    script_name = data["script"]
    print(f"will run script: {script_name}")
    script_file = script_dir / script_name
    args = [
        "python",
        script_file,
    ]
    with subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
        text=True,
    ) as proc:
        pid = proc.pid
        processes["current"] = proc   
        print(f"process started with pid: {pid}, extra data: {data}")
        # asyncio.create_task(read_process_output(proc, pid))
        # out_task = asyncio.create_task(read_pipe_output(proc.stdout, pid))
        # asyncio.run(read_process_output(proc, pid))
        await sio_app.emit("process_started", {"pid": pid})

        proc.wait()

        # await out_task
        await sio_app.emit("process_finished", {"pid": pid})
        processes.pop("current", None)


@sio_app.event
async def process_input(sid, data):
    pid = data["pid"]
    # proc = processes.get(pid)
    proc = processes.get("current")
    if proc is not None:
        proc.stdin.write(data["input"])
        proc.stdin.flush()
    else:
        print(f"process with pid {pid} not found")


async def read_process_output(proc, pid):
    try:
        while True:
            output = proc.stdout.readline()
            if not output:
                break
            await sio_app.emit("process_output", {"pid": pid, "output": output})
        proc.wait()

    except Exception as e:
        print(f"exception in read_process_output: {e}")

    finally:
        proc.stdout.close()
        proc.stderr.close()
        proc.stdin.close()
        processes.pop(pid, None)
        await sio_app.emit("process_finished", {"pid": pid})


async def read_pipe_output(pipe, pid):
    while pipe:
        output = pipe.readline()
        if not output:
            break
        await sio_app.emit("process_output", {"pid": pid, "output": output})