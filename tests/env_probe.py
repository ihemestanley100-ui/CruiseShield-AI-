"""Environment capability probes. The sandbox forbids socket creation
(WinError 10013), which also blocks asyncio loop creation on Windows.
Transport-dependent tests skip honestly here and run in CI/user envs."""
import socket


def _can_socketpair() -> bool:
    try:
        first, second = socket.socketpair()
    except OSError:
        return False
    first.close()
    second.close()
    return True


def _can_run_loop() -> bool:
    # On Windows every asyncio loop needs a socketpair/self-pipe, so probing
    # loop construction directly would only manufacture a broken loop object
    # that warns at GC time. Socket availability is the true gate here.
    return _can_socketpair()


CAN_SOCKETS = _can_socketpair()
CAN_LOOP = _can_run_loop()
