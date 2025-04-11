import win32serviceutil
import win32service
import win32event
import servicemanager
import sys
import os
import win32api
import win32con
import win32process
import win32ts
import win32profile
import time

class FullScreenAppService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FullScreenAppService"
    _svc_display_name_ = "Full Screen App Service"
    _svc_description_ = "Service to run the full screen PyQt5 app in user session"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process_handle = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        servicemanager.LogInfoMsg("Stopping service...")
        if self.process_handle:
            win32api.TerminateProcess(self.process_handle, 0)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        servicemanager.LogInfoMsg("Service start pending...")
        self.main()
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        servicemanager.LogInfoMsg("Service is running")

    def main(self):
        servicemanager.LogInfoMsg("Entering main function")
        # Получаем ID активной сессии пользователя
        session_id = win32ts.WTSGetActiveConsoleSessionId()
        if session_id == 0xFFFFFFFF:
            servicemanager.LogErrorMsg("No active user session found")
            return

        servicemanager.LogInfoMsg(f"Active session ID: {session_id}")

        # Получаем токен пользователя из сессии
        try:
            user_token = win32ts.WTSQueryUserToken(session_id)
            servicemanager.LogInfoMsg("User token obtained")
        except Exception as e:
            servicemanager.LogErrorMsg(f"Failed to get user token: {str(e)}")
            return

        # Путь к main.exe
        exe_path = r"C:\FullScreenApp\main.exe"
        if not os.path.exists(exe_path):
            servicemanager.LogErrorMsg(f"Executable not found at: {exe_path}")
            return

        servicemanager.LogInfoMsg(f"Executable path: {exe_path}")

        # Настраиваем среду для нового процесса
        env = win32profile.CreateEnvironmentBlock(user_token, False)
        servicemanager.LogInfoMsg("Environment block created")

        # Настраиваем параметры запуска
        si = win32process.STARTUPINFO()
        si.dwFlags = win32process.STARTF_USESHOWWINDOW
        si.wShowWindow = win32con.SW_SHOW

        # Запускаем main.exe в сессии пользователя
        try:
            self.process_handle, _, _, _ = win32process.CreateProcessAsUser(
                user_token,
                exe_path,
                None,
                None,
                None,
                False,
                win32process.CREATE_NEW_CONSOLE,
                env,
                None,
                si
            )
            servicemanager.LogInfoMsg("Process started successfully")
        except Exception as e:
            servicemanager.LogErrorMsg(f"Failed to start process: {str(e)}")
            return

        # Ожидаем остановки службы
        servicemanager.LogInfoMsg("Waiting for stop event")
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(FullScreenAppService)
        try:
            servicemanager.StartServiceCtrlDispatcher()
        except Exception as e:
            servicemanager.LogErrorMsg(f"Dispatcher failed: {str(e)}")
    else:
        win32serviceutil.HandleCommandLine(FullScreenAppService)