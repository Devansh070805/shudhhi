import subprocess
import os
import sys
import tempfile
import logging
import re
import platform


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class do_wipe:

    WIPE_TIMEOUT_SECONDS = 86400

    @staticmethod
    def _run_command(cmd, state_callback=None, pass_name="", use_shell=False):
        try:
            command_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
            logging.info(f"Executing command: {command_str}")

            process = subprocess.Popen(
                command_str if use_shell else cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                shell=use_shell
            )

            if state_callback:
                state_callback("wiping", message=f"Starting: {pass_name}")

            logs = []
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    clean_line = line.strip()
                    if clean_line:
                        logs.append(clean_line)
                        logging.info(f"[CMD_OUTPUT] {clean_line}")
                        if state_callback:
                            state_callback("logging", line=clean_line)
            process.stdout.close()

            return_code = process.wait(timeout=do_wipe.WIPE_TIMEOUT_SECONDS)
            output = "\n".join(logs)

            is_dd_command = " dd " in f" {command_str} "
            if is_dd_command and "No space left on device" in output:
                logging.warning("'dd' successfully filled the device, which is the desired outcome.")
                return True, "Wipe pass completed successfully by filling the device."

            if return_code != 0:
                raise subprocess.CalledProcessError(return_code, command_str, output=output)

            logging.info(f"Command executed successfully: {command_str}")
            return True, output

        except subprocess.TimeoutExpired:
            logging.error("Wipe process timed out. Terminating.")
            if 'process' in locals() and process.poll() is None:
                process.kill()
            return False, "The wipe process became unresponsive and was terminated."
        except subprocess.CalledProcessError as e:
            error_message = f"Process failed with code {e.returncode}. Output: {e.output}"
            logging.error(error_message)
            return False, error_message
        except FileNotFoundError:
            cmd_name = cmd[0] if isinstance(cmd, list) else cmd.split()[0]
            error_message = f"Error: The command '{cmd_name}' was not found. Please ensure it's installed and in your system's PATH."
            logging.error(error_message)
            return False, error_message
        except Exception as e:
            logging.error(f"An unexpected error occurred during command execution: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def _get_os_disk_path():
        os_type = platform.system()
        try:
            if os_type == "Linux":
                out = subprocess.check_output(['findmnt', '-n', '-o', 'SOURCE', '/'], text=True).strip()
                match = re.match(r'(/dev/(?:sd|hd|vd|xvd)[a-z]+|/dev/nvme[0-9]+n[0-9]+)', out)
                return match.group(1) if match else None
            elif os_type == "Darwin":
                out = subprocess.check_output(['diskutil', 'info', '/'], text=True).strip()
                match = re.search(r'Part of Whole:\s+(\w+)', out)
                return f"/dev/{match.group(1)}" if match else None
            elif os_type == "Windows":
                ps_cmd = '(Get-Partition -DriveLetter (Get-Volume -FilePath $env:SystemDrive).DriveLetter).DiskNumber'
                return subprocess.check_output(["powershell", "-Command", ps_cmd], text=True).strip()
        except (subprocess.CalledProcessError, FileNotFoundError, AttributeError, TypeError, IndexError) as e:
            logging.error(f"Failed to determine OS disk path on {os_type}: {e}")
            return None  # Fail safely

    @staticmethod
    def _master_safety_check(disk_identifier):
        os_disk = do_wipe._get_os_disk_path()
        if not os_disk:
            return False, "CRITICAL_ERROR: Could not determine the OS disk. Aborting for safety."

        target_norm = os.path.basename(disk_identifier).strip()
        os_disk_norm = os.path.basename(os_disk).strip()

        if platform.system() == "Windows":
            target_norm = ''.join(filter(str.isdigit, target_norm))

        if target_norm == os_disk_norm:
            error_msg = f"SAFETY_ERROR: Target disk '{disk_identifier}' is the active OS disk ('{os_disk}'). Aborting wipe."
            logging.critical(error_msg)
            return False, error_msg

        logging.info(f"Safety Check Passed: Target '{disk_identifier}' is not the OS disk '{os_disk}'.")
        return True, "Safety check passed."

    @staticmethod
    def _unmount_disk(disk_identifier):
        os_type = platform.system()
        logging.info(f"Attempting to unmount partitions on {disk_identifier} for {os_type}.")
        try:
            if os_type == "Linux":
                partitions_out = subprocess.check_output(
                    ["lsblk", "-ln", "-o", "NAME", disk_identifier], text=True
                ).strip().split('\n')[1:]
                for part in partitions_out:
                    logging.info(f"Unmounting /dev/{part}...")
                    subprocess.run(["umount", f"/dev/{part}"], check=False, capture_output=True)
            elif os_type == "Darwin":
                subprocess.run(
                    ["diskutil", "unmountDisk", disk_identifier], check=True, capture_output=True
                )
            return True
        except Exception as e:
            logging.warning(f"Could not unmount {disk_identifier}, proceeding with wipe. This may fail. Reason: {e}")
            return True 

    @staticmethod
    def _perform_wipe_passes(disk_identifier, passes, state_callback):
        if not do_wipe._unmount_disk(disk_identifier):
            return False, f"Failed to unmount {disk_identifier} before wiping. Aborting."

        total_passes = len(passes)
        for i, (pass_name, cmd, use_shell) in enumerate(passes):
            logging.info(f"--- Starting Pass {i+1}/{total_passes}: {pass_name} ---")
            if state_callback:
                state_callback("progress", current=i + 1, total=total_passes, message=f"Pass {i+1}/{total_passes}: {pass_name}")

            success, message = do_wipe._run_command(cmd, state_callback, pass_name, use_shell)
            if not success:
                error_msg = f"Wipe failed on Pass {i+1} ({pass_name}). Reason: {message}"
                logging.error(error_msg)
                return False, error_msg

        return True, "All wipe passes completed successfully."

    # Erasure Method Classes 

    class FillZeros:
        """Writes zeros to the entire disk (1 pass)."""
        @staticmethod
        def for_linux(disk_identifier: str, state_callback=None):
            success, msg = do_wipe._master_safety_check(disk_identifier)
            if not success: return False, msg
            passes = [("Fill with Zeros", ["dd", "if=/dev/zero", f"of={disk_identifier}", "bs=4M", "status=progress", "oflag=direct"], False)]
            return do_wipe._perform_wipe_passes(disk_identifier, passes, state_callback)

        @staticmethod
        def for_windows(disk_identifier: str, state_callback=None):
            success, msg = do_wipe._master_safety_check(disk_identifier)
            if not success: return False, msg
            script_path = None
            try:
                disk_number = ''.join(filter(str.isdigit, disk_identifier))
                script_content = f"select disk {disk_number}\nclean all"
                with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding='utf-8') as f:
                    script_path = f.name
                    f.write(script_content)
                return do_wipe._run_command(["diskpart", "/s", script_path], state_callback, "DiskPart Clean All")
            finally:
                if script_path and os.path.exists(script_path):
                    os.remove(script_path)

        @staticmethod
        def for_darwin(disk_identifier: str, state_callback=None):
            success, msg = do_wipe._master_safety_check(disk_identifier)
            if not success: return False, msg
            return do_wipe._run_command(["diskutil", "secureErase", "0", disk_identifier], state_callback, "Single-Pass Zero-Fill")

    class FillOnes:
        @staticmethod
        def for_linux(disk_identifier: str, state_callback=None):
            success, msg = do_wipe._master_safety_check(disk_identifier)
            if not success: return False, msg
            command = f"tr '\\0' '\\377' < /dev/zero | dd of={disk_identifier} bs=4M status=progress oflag=direct"
            passes = [("Fill with Ones", command, True)]
            return do_wipe._perform_wipe_passes(disk_identifier, passes, state_callback)

        @staticmethod
        def for_windows(disk_identifier: str, state_callback=None):
            return False, "Fill with Ones is not natively supported on Windows with built-in tools."

        @staticmethod
        def for_darwin(disk_identifier: str, state_callback=None):
            # macOS doesn't have a direct 'fill ones' but we can use the same Linux method.
            return do_wipe.FillOnes.for_linux(disk_identifier, state_callback)

    class PRNGStream:
        @staticmethod
        def for_linux(disk_identifier: str, state_callback=None):
            success, msg = do_wipe._master_safety_check(disk_identifier)
            if not success: return False, msg
            passes = [("Fill with Random Data", ["dd", "if=/dev/urandom", f"of={disk_identifier}", "bs=4M", "status=progress", "oflag=direct"], False)]
            return do_wipe._perform_wipe_passes(disk_identifier, passes, state_callback)

        @staticmethod
        def for_windows(disk_identifier: str, state_callback=None):
            return False, "Fill with PRNG stream is not natively supported on Windows with built-in tools."

        @staticmethod
        def for_darwin(disk_identifier: str, state_callback=None):
            success, msg = do_wipe._master_safety_check(disk_identifier)
            if not success: return False, msg
            return do_wipe._run_command(["diskutil", "secureErase", "1", disk_identifier], state_callback, "Single-Pass Random-Fill")

    class DoD_Short:
        @staticmethod
        def for_linux(disk_identifier: str, state_callback=None):
            success, msg = do_wipe._master_safety_check(disk_identifier)
            if not success: return False, msg
            passes = [
                ("Pass 1/3: Fill with Zeros", ["dd", "if=/dev/zero", f"of={disk_identifier}", "bs=4M", "oflag=direct"], False),
                ("Pass 2/3: Fill with Ones", f"tr '\\0' '\\377' < /dev/zero | dd of={disk_identifier} bs=4M oflag=direct", True),
                ("Pass 3/3: Fill with Random Data", ["dd", "if=/dev/urandom", f"of={disk_identifier}", "bs=4M", "oflag=direct"], False)
            ]
            return do_wipe._perform_wipe_passes(disk_identifier, passes, state_callback)

        @staticmethod
        def for_windows(disk_identifier: str, state_callback=None):
            return False, "DoD Short wipe is not natively supported on Windows."

        @staticmethod
        def for_darwin(disk_identifier: str, state_callback=None):
            success, msg = do_wipe._master_safety_check(disk_identifier)
            if not success: return False, msg
            return do_wipe._run_command(["diskutil", "secureErase", "3", disk_identifier], state_callback, "DoD 5220.22-M 3-Pass Wipe")

    class DoD_5220_22M:
        @staticmethod
        def for_linux(disk_identifier: str, state_callback=None):
            return False, "DoD 5220.22-M (7-pass) is complex and not recommended for implementation with shell tools. Use a dedicated utility like 'nwipe'."

        @staticmethod
        def for_windows(disk_identifier: str, state_callback=None):
            return False, "DoD 5220.22-M (7-pass) is not natively supported on Windows."

        @staticmethod
        def for_darwin(disk_identifier: str, state_callback=None):
            success, msg = do_wipe._master_safety_check(disk_identifier)
            if not success: return False, msg
            return do_wipe._run_command(["diskutil", "secureErase", "2", disk_identifier], state_callback, "DoD 5220.22-M 7-Pass Wipe")

    class Gutmann:
        @staticmethod
        def for_linux(disk_identifier: str, state_callback=None):
            return False, "Gutmann wipe (35 passes) is not practical with shell tools and is excessive for modern drives. Use a dedicated utility."

        @staticmethod
        def for_windows(disk_identifier: str, state_callback=None):
            return False, "Gutmann wipe is not natively supported on Windows."

        @staticmethod
        def for_darwin(disk_identifier: str, state_callback=None):
            success, msg = do_wipe._master_safety_check(disk_identifier)
            if not success: return False, msg
            return do_wipe._run_command(["diskutil", "secureErase", "4", disk_identifier], state_callback, "Gutmann 35-Pass Wipe")

    class HDParm:
        @staticmethod
        def for_linux(disk_identifier: str, state_callback=None):
            success, msg = do_wipe._master_safety_check(disk_identifier)
            if not success: return False, msg

            logging.warning("HDPARM SECURITY ERASE IS A DANGEROUS, FIRMWARE-LEVEL OPERATION. PROCEED WITH CAUTION.")

            # 1. Check drive security status. It must not be 'frozen'.
            status_cmd = ["hdparm", "-I", disk_identifier]
            success, output = do_wipe._run_command(status_cmd)
            if not success:
                return False, f"Could not get drive status: {output}"
            if "not frozen" not in output:
                return False, "Drive security is FROZEN. A power cycle (suspend/resume or reboot) is required before this command can be used."

            password = "p"  # A temporary password.
            erase_succeeded = False
            final_message = ""

            # 2. Set the security password.
            pass_cmd = ["hdparm", "--user-master", "u", "--security-set-pass", password, disk_identifier]
            success, msg = do_wipe._run_command(pass_cmd, state_callback, "Set Security Password")
            if not success:
                return False, f"Failed to set security password: {msg}"

            try:
                # 3. Issue the secure erase command.
                erase_cmd = ["hdparm", "--user-master", "u", "--security-erase", password, disk_identifier]
                success, msg = do_wipe._run_command(erase_cmd, state_callback, "Issue Secure Erase")
                if not success:
                    final_message = f"Secure erase command failed: {msg}"
                    erase_succeeded = False
                else:
                    final_message = "hdparm secure erase completed successfully."
                    erase_succeeded = True
            finally:
                # 4. CRITICAL FINAL STEP: ALWAYS attempt to disable the security password.
                logging.info("Attempting to disable drive security lock...")
                disable_cmd = ["hdparm", "--user-master", "u", "--security-disable", password, disk_identifier]
                disable_success, disable_msg = do_wipe._run_command(disable_cmd, state_callback, "Disable Security Password")

                if not disable_success:
                    if erase_succeeded:
                        return False, f"ERASE SUCCEEDED, BUT FAILED TO DISABLE SECURITY LOCK. The drive may be inaccessible. Message: {disable_msg}"
                    else:
                        return False, f"{final_message} AND failed to disable security lock. The drive may be inaccessible. Message: {disable_msg}"

            if erase_succeeded:
                return True, "hdparm secure erase completed and security disabled successfully."
            else:
                return False, f"{final_message} Security lock was successfully disabled."

        @staticmethod
        def for_windows(disk_identifier: str, state_callback=None):
            return True, "hdparm is a Linux-specific utility."

        @staticmethod
        def for_darwin(disk_identifier: str, state_callback=None):
            return False, "hdparm is not available on macOS."

