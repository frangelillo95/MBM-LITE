import os
import shutil
import threading
import time
from datetime import datetime

from . import app_state
from .logger import log, log_job
from .state import salva_stato

try:
    import winsound
except Exception:
    winsound = None


_jobs_lock = threading.Lock()


def safe_copy2(src_path, dst_path, retries=3, delay=0.5):
    """
    Safely copies a file using a temporary file and atomic replace.
    Retries on temporary copy errors.
    """
    tmp_path = dst_path + ".mbm_tmp"
    last_error = None

    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    for attempt in range(1, retries + 1):
        try:
            shutil.copy2(src_path, tmp_path)
            os.replace(tmp_path, dst_path)
            return True

        except Exception as e:
            last_error = e

            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

            if attempt < retries:
                log(
                    f"[Copy Retry] Failed to copy {src_path} -> {dst_path} "
                    f"on attempt {attempt}/{retries}: {e}. Retrying..."
                )
                time.sleep(delay)
            else:
                log(
                    f"[Copy Failed] Failed to copy {src_path} -> {dst_path} "
                    f"on final attempt {attempt}/{retries}: {e}"
                )

    raise last_error


def esegui_backup_incrementale(job):
    """
    Incremental backup engine.
    """

    try:
        stop_flag = job.get("stop_flag")
        if stop_flag is None:
            stop_flag = threading.Event()
            
        
        job["incomplete"] = True
        salva_stato()
        
        src, dst = job["source"], job["dest"]
        key = (src, dst)
        had_errors = False
        last_error = None

        

        with _jobs_lock:
            if key in app_state.jobs_in_esecuzione:
                log_job(f"[Skip] Backup already running for: {src} -> {dst}", src, dst)
                return

            app_state.jobs_in_esecuzione.add(key)
            app_state.job_errors.pop(key, None)
        try:
            from mbm_lite.gui.job_rows import refresh_job_rows

            root = getattr(app_state, "root", None)
            if root is not None:
                root.after(0, refresh_job_rows)
        except Exception:
            pass

        if key in app_state.progress_bars:
            try:
                app_state.progress_bars[key].config(value=0)
            except Exception:
                pass
       

        totale_file = 0
        for root_dir, _, files in os.walk(src):
            if os.path.abspath(root_dir).startswith(os.path.abspath(dst)):
                continue
            totale_file += len(files)

        count = 0
        if key in app_state.progress_bars:
            try:
                app_state.progress_bars[key].config(value=0)
            except Exception:
                pass

        for root_dir, _, files in os.walk(src):
            if stop_flag.is_set():
                log_job(f"[Stopped] Backup stopped for: {src} -> {dst}", src, dst)
                job["incomplete"] = True
                salva_stato()
                return

            root_abs = os.path.abspath(root_dir)
            dst_abs = os.path.abspath(dst)
            try:
                if os.path.commonpath([root_abs, dst_abs]) == dst_abs:
                    continue
            except ValueError:
                pass

            for file in files:
                if stop_flag.is_set():
                    log_job(f"[Stopped] Backup stopped for: {src} -> {dst}", src, dst)
                    job["incomplete"] = True
                    salva_stato()
                    return

                while job.get("paused", False) and not stop_flag.is_set():
                    time.sleep(0.2)

                if stop_flag.is_set():
                    log_job(f"[Stopped] Backup stopped for: {src} -> {dst}", src, dst)
                    job["incomplete"] = True
                    salva_stato()
                    return

                s = os.path.join(root_dir, file)
                d = os.path.join(dst, os.path.relpath(s, src))
                need_copy = False

                try:
                    s_mtime = os.path.getmtime(s)
                    if not os.path.exists(d):
                        need_copy = True
                    else:
                        d_mtime = os.path.getmtime(d)
                        if s_mtime > d_mtime:
                            need_copy = True
                    if need_copy:
                        os.makedirs(os.path.dirname(d), exist_ok=True)
                        safe_copy2(s, d)
                        log_job(f"[Backup] Copied/Updated: {s} -> {d}", src, dst)
                except Exception as e:
                    had_errors = True
                    last_error = e  
                    log_job(f"[Error] Skipping {s}: {e}", src, dst)

                count += 1
                if key in app_state.progress_bars and totale_file > 0:
                    try:
                        if job.get("paused", False):
                            app_state.progress_bars[key].config(style="yellow.Horizontal.TProgressbar")
                        else:
                            app_state.progress_bars[key].config(style="green.Horizontal.TProgressbar")
                        app_state.progress_bars[key].config(value=int((count / totale_file) * 100))
                        app_state.progress_bars[key].update_idletasks()
                    except Exception:
                        pass

        job["incomplete"] = False
        job["last_backup"] = datetime.now().isoformat()

        if had_errors:
            app_state.job_errors[key] = str(last_error)
            log_job(f"[Backup Completed With Errors] {src} -> {dst}", src, dst)
        else:
            app_state.job_errors.pop(key, None)
            log_job(f"[*] Backup completed for: {src} -> {dst}", src, dst)

        salva_stato()
        try:
            if winsound:
                winsound.MessageBeep()
        except Exception:
            pass
    except Exception as e:
        if "key" in locals():
            app_state.job_errors[key] = str(e)
        if "src" in locals() and "dst" in locals():
            log_job(f"[Backup Error] {e}", src, dst)
        else:
            log(f"[Backup Error] {e}")
        job["incomplete"] = True
        salva_stato()
    finally:
        if "key" in locals() and key in app_state.progress_bars:
            try:
                if not job.get("paused", False):
                    app_state.progress_bars[key].config(value=0)
            except Exception:
                pass
        if "key" in locals():
            with _jobs_lock:
                app_state.jobs_in_esecuzione.discard(key)
            try:
                from mbm_lite.gui.job_rows import refresh_job_rows

                root = getattr(app_state, "root", None)
                if root is not None:
                    root.after(0, refresh_job_rows)
            except Exception:
                pass


def esegui_backup_forzato_incrementale(job):
    """
    Forced incremental backup: never deletes files, only adds or updates newer files.
    """
    try:
        job["incomplete"] = True
        salva_stato()
        src, dst = job["source"], job["dest"]
        key = (src, dst)
        had_errors = False
        last_error = None


        with _jobs_lock:
            if key in app_state.jobs_in_esecuzione:
                log_job(f"[Skip] Backup already running for: {src} -> {dst}", src, dst)
                return
            app_state.jobs_in_esecuzione.add(key)
            app_state.job_errors.pop(key, None)
        try:
            from mbm_lite.gui.job_rows import refresh_job_rows

            root = getattr(app_state, "root", None)
            if root is not None:
                root.after(0, refresh_job_rows)
        except Exception:
            pass

        stop_flag = job.get("stop_flag")
        if stop_flag is None:
            stop_flag = threading.Event()
            

        totale_file = 0
        for root_dir, _, files in os.walk(src):
            if os.path.abspath(root_dir).startswith(os.path.abspath(dst)):
                continue
            totale_file += len(files)

        count = 0
        if key in app_state.progress_bars:
            try:
                app_state.progress_bars[key].config(value=0)
            except Exception:
                pass

        for root_dir, _, files in os.walk(src):
            if stop_flag.is_set():
                log_job(f"[Stopped] Backup stopped for: {src} -> {dst}", src, dst)
                job["incomplete"] = True
                salva_stato()
                return

            root_abs = os.path.abspath(root_dir)
            dst_abs = os.path.abspath(dst)
            try:
                if os.path.commonpath([root_abs, dst_abs]) == dst_abs:
                    continue
            except ValueError:
                pass

            for file in files:
                while job.get("paused", False) and not stop_flag.is_set():
                    time.sleep(0.2)

                if stop_flag.is_set():
                    log_job(f"[Stopped] Backup stopped for: {src} -> {dst}", src, dst)
                    job["incomplete"] = True
                    salva_stato()
                    return

                s = os.path.join(root_dir, file)
                d = os.path.join(dst, os.path.relpath(s, src))
                try:
                    s_mtime = os.path.getmtime(s)
                except FileNotFoundError:
                    continue

                if os.path.exists(d):
                    try:
                        d_mtime = os.path.getmtime(d)
                        if s_mtime > d_mtime:
                            os.makedirs(os.path.dirname(d), exist_ok=True)
                            safe_copy2(s, d)
                            log_job(f"[Backup] Updated: {s} -> {d}", src, dst)
                    except Exception as e:
                        had_errors = True
                        last_error = e
                        log_job(f"[Error] Cannot update {d}: {e}", src, dst)
                else:
                    os.makedirs(os.path.dirname(d), exist_ok=True)
                    safe_copy2(s, d)
                    log_job(f"[Backup] New: {s} -> {d}", src, dst)

                count += 1
                if key in app_state.progress_bars and totale_file > 0:
                    try:
                        if job.get("paused", False):
                            app_state.progress_bars[key].config(style="yellow.Horizontal.TProgressbar")
                        else:
                            app_state.progress_bars[key].config(style="green.Horizontal.TProgressbar")
                        app_state.progress_bars[key].config(value=int((count / totale_file) * 100))
                        app_state.progress_bars[key].update_idletasks()
                    except Exception:
                        pass

        job["incomplete"] = False
        job["last_backup"] = datetime.now().isoformat()
        salva_stato()
        log_job(f"[*] Backup completed for: {src} -> {dst}", src, dst)
        try:
            if winsound:
                winsound.MessageBeep()
        except Exception:
            pass
    except Exception as e:
        if "key" in locals():
            app_state.job_errors[key] = str(e)
        if "src" in locals() and "dst" in locals():
            log_job(f"[Backup error] {e}", src, dst)
        else:
            log(f"[Backup error] {e}")
        job["incomplete"] = True
        salva_stato()
    finally:
        if "key" in locals() and key in app_state.progress_bars:
            try:
                if not job.get("paused", False):
                    app_state.progress_bars[key].config(value=0)
            except Exception:
                pass
        if "key" in locals():
            with _jobs_lock:
                app_state.jobs_in_esecuzione.discard(key)
            try:
                from mbm_lite.gui.job_rows import refresh_job_rows

                root = getattr(app_state, "root", None)
                if root is not None:
                    root.after(0, refresh_job_rows)
            except Exception:
                pass
