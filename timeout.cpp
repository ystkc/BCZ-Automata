// Encoding: GBK
// Compile: [g++/gcc] timeout.cpp -o timeout.exe -m32 -lPowrProf (-mwindows)
// Compress: upx --best --overlay=strip timeout.exe
// Test Platform: Win11
#define _WIN32_WINNT 0x0600
#pragma GCC optimize(1)
#pragma GCC optimize(2)
#pragma GCC optimize(3, "Ofast", "inline")
// #define _LOG_ // Enable log output
#include <windows.h>
#include <initguid.h>
//initguid.h should be included before powrprof.h
#include <powrprof.h>
#ifdef _LOG_
    #include <stdio.h>
#endif

#pragma comment(lib, "PowrProf.lib")

int set_sleep_never(GUID GUID_BALANCED_POWER_POLICY) {
    SYSTEM_POWER_POLICY policy;
    ZeroMemory(&policy, sizeof(policy));
    if (PowerWriteACValueIndex(NULL, &GUID_BALANCED_POWER_POLICY, &GUID_SLEEP_SUBGROUP, &GUID_STANDBY_TIMEOUT, 0) == ERROR_SUCCESS &&
        PowerWriteDCValueIndex(NULL, &GUID_BALANCED_POWER_POLICY, &GUID_SLEEP_SUBGROUP, &GUID_STANDBY_TIMEOUT, 0) == ERROR_SUCCESS) {
#ifdef _LOG_
        puts("Sleep time has been set to never.");
#endif
        return 0;
    } else {
#ifdef _LOG_
        puts("Failed to set sleep time.");
#endif
        return 1;
    }
}



// GUID_VIDEO_TIMEOUT 
DEFINE_GUID(GUID_VIDEO_TIMEOUT, 
0x3c0bc021, 0xc8a8, 0x4e07, 0xa9, 0x73, 0x6b, 0x14, 0xcb, 0xcb, 0x2b, 0x7e);

// GUID_VIDEO_SUBGROUP
DEFINE_GUID(GUID_VIDEO_SUBGROUP, 
0x7516b95f, 0xf776, 0x4464, 0x8c, 0x53, 0x06, 0x16, 0x7f, 0x40, 0xcc, 0x99);

// GUID_SLEEP_SUBGROUP 
DEFINE_GUID(GUID_SLEEP_SUBGROUP, 
0x238c9fa8, 0x0aad, 0x41ed, 0x83, 0xf4, 0x97, 0xbe, 0x24, 0x2c, 0x8f, 0x20);

// GUID_STANDBY_TIMEOUT
DEFINE_GUID(GUID_STANDBY_TIMEOUT, 
0x29f6c1db, 0x86da, 0x48c5, 0x9f, 0xdb, 0xf2, 0xb6, 0x7b, 0x1f, 0x44, 0xda);

//Power plans
// (Balanced):
//381b4222-f694-41f0-9685-ff5bb260df2e
GUID GUID_BALANCED = { 0x381b4222, 0xf694, 0x41f0, { 0x96, 0x85, 0xff, 0x5b, 0xb2, 0x60, 0xdf, 0x2e } };

// (High Performance):
//8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
GUID GUID_HIGH_PERFORMANCE = { 0x8c5e7fda, 0xe8bf, 0x4a96, { 0x9a, 0x85, 0xa6, 0xe2, 0x3a, 0x8c, 0x63, 0x5c } };

// (Power Saver):
//a1841308-3541-4fab-bc81-f71556f20b4a
GUID GUID_POWER_SAVER = { 0xa1841308, 0x3541, 0x4fab, { 0xbc, 0x81, 0xf7, 0x15, 0x56, 0xf2, 0x0b, 0x4a } };

int set_screen_timeout_never(GUID GUID_TARGET) {
    // Both AC and DC mode
    if (PowerWriteACValueIndex(
            NULL,
            &GUID_TARGET,    
            &GUID_VIDEO_SUBGROUP,         
            &GUID_VIDEO_TIMEOUT,           
            0) == ERROR_SUCCESS &&
        PowerWriteDCValueIndex(
            NULL,
            &GUID_TARGET,
            &GUID_VIDEO_SUBGROUP,
            &GUID_VIDEO_TIMEOUT,
            0) == ERROR_SUCCESS) {
        // Apply the new power scheme
        if (PowerSetActiveScheme(NULL, &GUID_TARGET) == ERROR_SUCCESS) {
#ifdef _LOG_
            puts("Screen timeout has been set to never.");
#endif
            return 0;
        } else {
#ifdef _LOG_
            puts("Failed to apply power scheme.");
#endif
            return 2;
        }
    } else {
#ifdef _LOG_
            puts("Failed to set screen timeout.");
#endif
            return 3;
    }
}

int set_lid_close_action() {
    HKEY hKey;
    LPCSTR path = "SYSTEM\\CurrentControlSet\\Control\\Power";
    if (RegOpenKeyExA(HKEY_LOCAL_MACHINE, path, 0, KEY_WRITE, &hKey) == ERROR_SUCCESS) {
        DWORD data_sleep = 0x00000001; // No action 

        // AC
        if (RegSetValueExA(hKey, "LidCloseAction", 0, REG_DWORD, (BYTE*)&data_sleep, sizeof(data_sleep)) == ERROR_SUCCESS) {
#ifdef _LOG_
            puts("Lid close action (AC mode) has been set to no action.");
#endif
            return 0;
        } else {
#ifdef _LOG_
            puts("Failed to set lid close action (AC mode).");
#endif
            return 4;
        }

        // DC
        if (RegSetValueExA(hKey, "LidCloseAction_DC", 0, REG_DWORD, (BYTE*)&data_sleep, sizeof(data_sleep)) == ERROR_SUCCESS) {
#ifdef _LOG_
            puts("Lid close action (DC mode) has been set to no action.");
#endif
            return 0;
        } else {
#ifdef _LOG_
            puts("Failed to set lid close action (DC mode).");
#endif
            return 5;
        }
        RegCloseKey(hKey);
    } else {
#ifdef _LOG_
        puts("Could not open the registry.");
#endif
        return 6;
    }
}

// Below are the settings functions in reverse mode
int set_screen_timeout_3min(GUID GUID_TARGET) {
    DWORD timeout = 180; // 3 minutes
    if (PowerWriteACValueIndex(NULL, &GUID_TARGET, &GUID_VIDEO_SUBGROUP, &GUID_VIDEO_TIMEOUT, timeout) == ERROR_SUCCESS &&
        PowerWriteDCValueIndex(NULL, &GUID_TARGET, &GUID_VIDEO_SUBGROUP, &GUID_VIDEO_TIMEOUT, timeout) == ERROR_SUCCESS) {
        if (PowerSetActiveScheme(NULL, &GUID_TARGET) == ERROR_SUCCESS) {
#ifdef _LOG_
            puts("Screen timeout has been set to 3 minutes.");
#endif
            return 0;
        } else {
#ifdef _LOG_
            puts("Failed to apply power scheme.");
#endif
            return 7;
        }
    } else {
#ifdef _LOG_
            puts("Failed to set screen timeout.");
#endif
            return 8;
    }
}

int set_sleep_3min(GUID GUID_TARGET) {
    DWORD timeout = 180; // 3 minutes
    if (PowerWriteACValueIndex(NULL, &GUID_TARGET, &GUID_SLEEP_SUBGROUP, &GUID_STANDBY_TIMEOUT, timeout) == ERROR_SUCCESS &&
        PowerWriteDCValueIndex(NULL, &GUID_TARGET, &GUID_SLEEP_SUBGROUP, &GUID_STANDBY_TIMEOUT, timeout) == ERROR_SUCCESS) {
#ifdef _LOG_
            puts("Sleep time has been set to 3 minutes.");
#endif
            return 0;
        } else {
#ifdef _LOG_
            puts("Failed to set sleep time.");
#endif
            return 9;
        }
}

int set_lid_close_sleep() {
    HKEY hKey;
    LPCSTR path = "SYSTEM\\CurrentControlSet\\Control\\Power";
    if (RegOpenKeyExA(HKEY_LOCAL_MACHINE, path, 0, KEY_WRITE, &hKey) == ERROR_SUCCESS) {
        DWORD data_sleep = 0x00000002; // Sleep
        // AC
        if (RegSetValueExA(hKey, "LidCloseAction", 0, REG_DWORD, (BYTE*)&data_sleep, sizeof(data_sleep)) == ERROR_SUCCESS) {
#ifdef _LOG_
            puts("Lid close action (AC mode) has been set to sleep.");
#endif
            return 0;
        } else {
#ifdef _LOG_
            puts("Failed to set lid close action (AC mode).");
#endif
            return 10;
        }
        // DC
        if (RegSetValueExA(hKey, "LidCloseAction_DC", 0, REG_DWORD, (BYTE*)&data_sleep, sizeof(data_sleep)) == ERROR_SUCCESS) {
#ifdef _LOG_
            puts("Lid close action (DC mode) has been set to sleep.");
#endif
            return 0;
        } else {
#ifdef _LOG_
            puts("Failed to set lid close action (DC mode).");
#endif
            return 11;
        }
        RegCloseKey(hKey);
    } else {
#ifdef _LOG_
        puts("Could not open the registry.");
#endif
        return 12;
    }
}

int main(int argc, char* argv[]) {
    // No parameters: prevent sleep; reverse: allow sleep;
    int status_code = 0;
    if (argc == 2 && strcmp(argv[1], "reverse") == 0) {
#ifdef _LOG_
        puts("Allowing sleep...");
#endif
        status_code = set_sleep_3min(GUID_POWER_SAVER);
        if (status_code != 0) return status_code;
        status_code = set_screen_timeout_3min(GUID_POWER_SAVER);
        if (status_code != 0) return status_code;
        status_code = set_sleep_3min(GUID_BALANCED);
        if (status_code != 0) return status_code;
        status_code = set_screen_timeout_3min(GUID_BALANCED);
        if (status_code != 0) return status_code;
#ifdef _LOG_
        puts("Will change the registry to set lid close to sleep mode.");
#endif
        status_code = set_lid_close_sleep();
        if (status_code != 0) return status_code;
    } else {
#ifdef _LOG_
        puts("Preventing sleep... Add 'reverse' parameter to undo changes.");
#endif
        status_code = set_sleep_never(GUID_BALANCED);
        if (status_code != 0) return status_code;
        status_code = set_screen_timeout_never(GUID_BALANCED);
        if (status_code != 0) return status_code;
        status_code = set_sleep_never(GUID_POWER_SAVER);
        if (status_code != 0) return status_code;
        status_code = set_screen_timeout_never(GUID_POWER_SAVER);
        if (status_code != 0) return status_code;
#ifdef _LOG_
        puts("Will change the registry to set lid close to no sleep.");
#endif
        status_code = set_lid_close_action();
        if (status_code != 0) return status_code;
    }
    return 0;
}
