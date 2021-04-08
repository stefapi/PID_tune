#!/usr/bin/env python

#   Copyright (c) 2021  stef
#  BSD Simplified License
#
#   Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
#   following conditions are met:
#   1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#   disclaimer.
#   2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#   following disclaimer in the documentation and/or other materials provided with the distribution.
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
#   INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
#   WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
#   USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# ----------------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <florian.melsheimer@gmx.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. Florian Melsheimer
# ----------------------------------------------------------------------------------

import argparse
import logging
import logging.handlers
import os
import sys
import time
import matplotlib.pyplot as plt
from six.moves import input as sinput

from pid_tune.blackbox_log import blackbox_log
from pid_tune import __version__
from pid_tune.treat_data import treat_data

Version = 'pid_tune ' + __version__


def run_analysis(log_file_path, plot_name, noise_bounds, use_motors_as_throttle, noise_cmap, fig_resp, fig_noise):
    logs = blackbox_log(log_file_path, plot_name, use_motors_as_throttle)
    for head, data in zip(logs.heads, logs.datas):
        try:
            analysed = treat_data(head, data, plot_name, logs.correctdebugmode, noise_bounds, use_motors_as_throttle, noise_cmap, fig_resp, fig_noise)
        except:
            logging.error('_csv_iter: CSV_log failed %s-%s failed' % (head['tempFile'], head['logNum']), exc_info=True)
    logging.info('Analysis complete, showing plot. (Close plot to exit.)')


def strip_quotes(filepath):
    """Strips single or double quotes and extra whitespace from a string."""
    return filepath.strip().strip("'").strip('"')


def clean_path(path):
    return os.path.abspath(os.path.expanduser(strip_quotes(path)))


def run_interactive(show_gui, noise_bounds, use_motors_as_throttle, noise_cmap, fig_resp, fig_noise):
    logging.info('Interactive mode: Enter log file, or type "close" when done.')
    while True:
        try:
            time.sleep(0.1)
            raw_path = sinput('Blackbox log file path (type or drop here). Type "close" to end: ')

            if raw_path == 'close':
                logging.info('Goodbye!')
                break

            raw_paths = strip_quotes(raw_path).replace("''", '""').split('""')  # seperate multiple paths
            name = sinput('plot name:')

            noise_bounds_str = sinput('Bounds on noise plot: [default/last] | copy and edit | "auto"\nCurrent: '+str(noise_bounds)+'\n')

            if noise_bounds_str:
                try:
                    noise_bounds=eval(noise_bounds_str)
                except:
                    pass

        except (EOFError, KeyboardInterrupt):
            logging.info('Goodbye!')
            break

        logging.info('name:%s, show_gui:%s, noise_bounds:%s' % (name, show_gui, noise_bounds))
        for p in raw_paths:
            if os.path.isfile(clean_path(p)):
                run_analysis(clean_path(p), name, noise_bounds, use_motors_as_throttle, noise_cmap, fig_resp, fig_noise)
            else:
                logging.info('No valid input path!')

        if show_gui:
            plt.show()
        else:
            plt.cla()
            plt.clf()


def main():
    logging.basicConfig( format='%(levelname)s %(asctime)s %(filename)s:%(lineno)s: %(message)s', level=logging.INFO)

    handler = logging.handlers.RotatingFileHandler("pid_tune.log", mode='a', maxBytes=1048576, backupCount=1, encoding="utf8")
    rootLogger = logging.getLogger()
    rootLogger.addHandler(handler)

    logging.info(Version)

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    #Name of folder and plot
    parser.add_argument('-n', '--name', default='tmp', help='Plot name.')

    parser.add_argument('-q', '--quiet', action="store_true", help="Do not show GUI windows, only generate pictures.")
    parser.add_argument('-m', '--motors', action="store_true", help="Use motors max as throttle instead of rcCommand to analyze motor test bench logs.")
    parser.add_argument('-i', '--interactive', action="store_true", help="Enter log names interactively")
    parser.add_argument('-nn', '--no_noise_plot', default=False, action="store_true", help='do not render noise plot')
    parser.add_argument('-nr', '--no_response_plot', default=False, action="store_true", help='do not render set response plot')

    parser.add_argument('-s', '--show', default='N', help='Y = show plot window when done.\nN = Do not. \nDefault = N')

    #Noise Bounds
    parser.add_argument('-nb', '--noise_bounds', default='[[1.,20.1],[1.,20.],[1.,20.],[0.,4.]]', help='bounds of plots in noise analysis. use "auto" for autoscaling. \n default=[[1.,20.1],[1.,20.],[1.,20.],[0.,4.]]')
    parser.add_argument('-nc', '--noise_cmap', default='viridis', help='Noise plots color map, see "images" dir for vaild values\nhttps://matplotlib.org/3.1.0/tutorials/colors/colormaps.html\nDefault = viridis')
    parser.add_argument('files', nargs='*')

    args = parser.parse_args()

    try:
        args.noise_bounds = eval(args.noise_bounds)

    except:
        args.noise_bounds = args.noise_bounds

    #if not args.interactive and not args.files:
    #    parser.print_usage()
    #    sys.exit(1)


    show_gui = not args.quiet


    if args.interactive:
        run_interactive(show_gui, args.noise_bounds, args.motors, args.noise_cmap, args.no_response_plot != True, args.no_noise_plot != True)
        sys.exit()

    if args.files:
        for log_path in args.files:
            try:
                run_analysis(clean_path(log_path), args.name, args.noise_bounds, args.motors, args.noise_cmap, args.no_response_plot != True, args.no_noise_plot != True)
            except Exception as e:
                logging.error('run_analysis failed for %s' % log_path, exc_info=True)
        if show_gui:
            plt.show()
        else:
            plt.cla()
            plt.clf()
        sys.exit()

    else:
        run_interactive(show_gui, args.noise_bounds, args.motors, args.noise_cmap, args.no_response_plot != True, args.no_noise_plot != True)
        sys.exit()
