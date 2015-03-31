#!/usr/bin/env python
import os, sys, commands, re, time
from datetime import datetime

from dateutil.tz import tzlocal
import daemon


log_file_dir = os.path.abspath(sys.argv[1]) if sys.argv[1] != '-' else '-'
timeout = float(sys.argv[2] if len(sys.argv) >= 3 else 60)


def is_active(app, title):
    if (app == "desktop_window.Nautilus") and (title == "Desktop"):
        return False

    if 'is active' in commands.getoutput("gnome-screensaver-command -q"):
        return False

    if 'lockscreen' in commands.getoutput("ps ax | grep [l]ockscreen"):
        return False

    return True

def get_active_program():
    active_window_string = commands.getoutput("xprop -root | grep '_NET_ACTIVE_WINDOW(WINDOW)'")
    active = re.findall(r'#\s+0x(\w+)', active_window_string)[0]
    active = "0x" + "0" * (8-len(active)) + active

    program = commands.getoutput("wmctrl -lx | grep %s" % active).splitlines()[0]
    _, _, app, _, title = program.split(None, 4)
    return app, title

def get_timestamp():
    #    return datetime.now(tzlocal()).strftime('%Y-%m-%d_%T%Z')
    return commands.getoutput("date +'%Y-%m-%d_%H-%M-%S'")


with daemon.DaemonContext():
    should_print_screensaver = True
    should_print = True
    cur_date = ""
    time_of_screensaver_start = 0
    while True:
        try:
            cur_timestamp = get_timestamp()
            cur_date = cur_timestamp.split("_")[0]
            app, title = get_active_program()
            if is_active(app, title):
                log_line = '%s\t%-30s\t%s\n' % (cur_timestamp, app, title)

                if not should_print_screensaver:
                    dt_sleep = time.time() - time_of_screensaver_start
                    if (dt_sleep > 60):
                        time_of_screensaver_start = 0
                        log_line_from_screensaver_work = "rest {} min??????????????????????????????".format(int(dt_sleep/60))
                        log_line = log_line_from_screensaver_work + "\n\n" + log_line
                        pass

		should_print_screensaver = True
		should_print = True
            else:
                if should_print_screensaver:
                    time_of_screensaver_start = time.time()

                log_line = '%s\t%-30s\t%s\n' % (cur_timestamp, "Screensaver", "\n\n\n")
		should_print = should_print_screensaver
		should_print_screensaver = False


            if should_print:
                if log_file_dir == '-':
                    print log_line,
                else:
                    log_file = os.path.join(log_file_dir, "winlog_" + cur_date)
                    with open(log_file, 'a') as f:
                        f.write(log_line)
        except Exception:
            import traceback
            err_file = os.path.join(log_file_dir, "winlog_" + cur_date + ".err")
            with open(err_file, 'a') as f:
                traceback.print_exc(None, f);

        time.sleep(timeout)
