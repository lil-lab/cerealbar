""" Utilities for connecting to the Unity process.

Constants:
    WINDOWS_OS (str): The name of the Windows operating system.
    LINUX_OS (str): The name of the Linux operating system.
    MAC_OS (str): The name of the Mac operating system.
    WINDOWS_EXEC_NAME (str): The name of the game executable on Windows.
    LINUX_EXEC_NAME (str): The name of the game executable on Linux.
    MAC_EXEC_NAME (str): The name of the game executable on Mac.

Methods:
    start_standalone ([[], Popen): Starts the standalone process.
    quit_standalone([[Popen],]): Quits a standalone process.
"""
import platform
from subprocess import Popen, call

WINDOWS_OS: str = 'Windows'
LINUX_OS: str = 'Linux'
MAC_OS: str = 'Darwin'

WINDOWS_EXEC_NAME = 'Cereal-Bar'
LINUX_EXEC_NAME = './linux-build/Cereal-Bar.x86_64'
MAC_EXEC_NAME = 'Cereal-Bar.app'


def start_standalone() -> Popen:
    """ Starts the standalone process and returns a Popen object representing the new process.

    Raises:
        ValueError, if the OS is unrecognized.
    """
    system_os: str = platform.system()
    print('Starting standalone with system OS: ' + system_os)

    if system_os == WINDOWS_OS:
        return Popen(WINDOWS_EXEC_NAME)
    elif system_os == LINUX_OS:
        return Popen(LINUX_EXEC_NAME)
    elif system_os == MAC_OS:
        return Popen(["open", MAC_EXEC_NAME])
    else:
        raise ValueError('Unrecognized OS: ' + system_os)


def quit_standalone(old_process: Popen) -> None:
    """ Quits an existing Popen process.

    Raises:
        ValueError, if the OS is unrecognized.
    """
    old_process.kill()

    system_os: str = platform.system()
    if system_os == WINDOWS_OS or system_os == LINUX_OS:
        old_process.wait()
    elif system_os == MAC_OS:
        call(['osascript', '-e', 'quit app "' + MAC_EXEC_NAME + '"'])
    else:
        raise ValueError('Unrecognized OS: ' + system_os)
