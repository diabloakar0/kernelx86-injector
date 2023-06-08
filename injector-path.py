import os
import sys
import mmap
import ctypes

# İnject edilecek dosyanın yolu buraya girilecektir.
file_path = "C:\\path\\to\\your\\file.dll"

kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)

OpenProcess = kernel32.OpenProcess
VirtualAllocEx = kernel32.VirtualAllocEx
WriteProcessMemory = kernel32.WriteProcessMemory
CreateRemoteThread = kernel32.CreateRemoteThread

# target yolu
target_process_name = "target.exe"
dll_path = os.path.abspath(file_path)

def get_process_id(process_name):
    process_id = None
    process_snap = kernel32.CreateToolhelp32Snapshot(2, 0)
    entry = ctypes.Structure()
    entry.dwSize = ctypes.sizeof(entry)
    if kernel32.Process32First(process_snap, ctypes.byref(entry)):
        while kernel32.Process32Next(process_snap, ctypes.byref(entry)):
            if entry.szExeFile.decode().lower() == process_name.lower():
                process_id = entry.th32ProcessID
                break
    kernel32.CloseHandle(process_snap)
    return process_id

def inject_dll(process_id, dll_path):
    process_handle = OpenProcess(0x1F0FFF, False, process_id)
    if not process_handle:
        print("Süreç açılamadı")
        return False
    dll_size = len(dll_path) + 1
    remote_buffer = VirtualAllocEx(process_handle, 0, dll_size, 0x1000, 0x40)
    if not remote_buffer:
        print("Uzak bellek alanı ayrılamadı")
        kernel32.CloseHandle(process_handle)
        return False
    written = ctypes.c_ulong(0)
    if not WriteProcessMemory(process_handle, remote_buffer, dll_path, dll_size, ctypes.byref(written)):
        print("Belleğe yazma başarısız")
        kernel32.CloseHandle(process_handle)
        return False
    thread_id = ctypes.c_ulong(0)
    if not CreateRemoteThread(process_handle, None, 0, kernel32.LoadLibraryA, remote_buffer, 0, ctypes.byref(thread_id)):
        print("Uzak iş parçacığı oluşturulamadı")
        kernel32.CloseHandle(process_handle)
        return False
    print("DLL başarıyla enjekte edildi")
    kernel32.CloseHandle(process_handle)
    return True

def main():
    process_id = get_process_id(target_process_name)
    if process_id:
        inject_dll(process_id, dll_path)
    else:
        print("Hedef süreç bulunamadı")

if __name__ == "__main__":
    main()
