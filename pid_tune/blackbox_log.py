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

import logging
import os

import numpy as np
import pandas as pd

from pid_tune.orangebox import Parser
from pid_tune.orangebox.types import FrameType

LOG_MIN_BYTES = 500000

class blackbox_log:
    def __init__(self, log_file_path, name, use_motors_as_throttle):

        self.use_motors_as_throttle=use_motors_as_throttle

        self.tmp_dir = os.path.join(os.path.dirname(log_file_path), name)
        if not os.path.isdir(self.tmp_dir):
            os.makedirs(self.tmp_dir)

        loglist = self.decode(log_file_path)
        self.datas = [self.read_data(x[2]) for x in loglist]
        self.heads = self.getheader(loglist)

    def read_data(self, data):
        datdic={}
        ### keycheck for 'usecols' only reads usefull traces, uncommend if needed
        wanted =  ['time (us)','time',
                   'rcCommand[0]', 'rcCommand[1]', 'rcCommand[2]', 'rcCommand[3]',
                   'axisP[0]','axisP[1]','axisP[2]',
                   'axisI[0]', 'axisI[1]', 'axisI[2]',
                   'axisD[0]', 'axisD[1]','axisD[2]',
                   'gyroADC[0]', 'gyroADC[1]', 'gyroADC[2]',
                   'gyroData[0]', 'gyroData[1]', 'gyroData[2]',
                   'ugyroADC[0]', 'ugyroADC[1]', 'ugyroADC[2]',
                   #'accSmooth[0]','accSmooth[1]', 'accSmooth[2]',
                   'debug[0]', 'debug[1]', 'debug[2]','debug[3]',
                   'motor[0]', 'motor[1]', 'motor[2]', 'motor[3]',
                   #'energyCumulative (mAh)','vbatLatest (V)', 'amperageLatest (A)'
                   ]
        datdic.update({'time_us': data['time (us)'].values * 1e-6 if 'time (us)' in data.columns else data['time'].values * 1e-6})
        datdic.update({'throttle': data['rcCommand[3]'].values})

        self.correctdebugmode = not np.any(data['debug[3]']) # if debug[3] contains data, debug_mode is not correct for plotting

        if self.use_motors_as_throttle:
            motormax = np.maximum(data['motor[0]'].values, data['motor[1]'].values)
            motormax = np.maximum(motormax, data['motor[2]'].values)
            motormax = np.maximum(motormax, data['motor[3]'].values)
            datdic.update({'motormax': motormax})

        for i in ['0', '1', '2']:
            datdic.update({'rcCommand' + i: data['rcCommand['+i+']'].values})
            #datdic.update({'PID loop in' + i: data['axisP[' + i + ']'].values})
            try:
                datdic.update({'debug' + i: data['debug[' + i + ']'].values})
            except:
                logging.warning('No debug['+str(i)+'] trace found!')
                datdic.update({'debug' + i: np.zeros_like(data['rcCommand[' + i + ']'].values)})

            # get P trace (including case of missing trace)
            try:
                datdic.update({'PID loop in' + i: data['axisP[' + i + ']'].values})
            except:
                logging.warning('No P['+str(i)+'] trace found!')
                datdic.update({'PID loop in' + i: np.zeros_like(data['rcCommand[' + i + ']'].values)})

            try:
                datdic.update({'d_err'+i: data['axisD[' + i+']'].values})
            except:
                logging.warning('No D['+str(i)+'] trace found!')
                datdic.update({'d_err' + i: np.zeros_like(data['rcCommand[' + i + ']'].values)})

            try:
                datdic.update({'I_term'+i: data['axisI[' + i+']'].values})
            except:
                if i<2:
                    logging.warning('No I['+str(i)+'] trace found!')
                datdic.update({'I_term' + i: np.zeros_like(data['rcCommand[' + i + ']'].values)})

            datdic.update({'PID sum' + i: datdic['PID loop in'+i]+datdic['I_term'+i]+datdic['d_err'+i]})
            if 'gyroADC[0]' in data.keys():
                datdic.update({'gyroData' + i: data['gyroADC[' + i+']'].values})
            elif 'gyroData[0]' in data.keys():
                datdic.update({'gyroData' + i: data['gyroData[' + i+']'].values})
            elif 'ugyroADC[0]' in data.keys():
                datdic.update({'gyroData' + i: data['ugyroADC[' + i+']'].values})
            else:
                logging.warning('No gyro trace found!')
        return datdic

    def getheader(self, loglist):
        heads = []
        for i, bblog in enumerate(loglist):
            ### in case info is not provided by log, empty str is printed in plot
            headsdict = {'tempFile'     :'',
                         'craftName'   :'',
                         'fwType': '',
                         'version'     :'',
                         'date'        :'',
                         'rcRate'      :'',
                         'rcExpo'       :'',
                         'rates'        :'',
                         'rollPID'     :'',
                         'pitchPID'    :'',
                         'yawPID'      :'',
                         'deadBand'    :'',
                         'yawDeadBand' :'',
                         'logNum'       :'',
                         'tpa_breakpoint':'0',
                         'minThrottle':'',
                         'maxThrottle': '',
                         'tpa_percent':'',
                         'feedforward_weight':'',
                         'vbatComp':'',
                         'gyro_lpf':'',
                         'gyro_lowpass_type':'',
                         'gyro_lowpass_hz':'',
                         'gyro_notch_hz':'',
                         'gyro_notch_cutoff':'',
                         'dterm_filter_type':'',
                         'dterm_lpf_hz':'',
                         'yaw_lpf_hz':'',
                         'dterm_notch_hz':'',
                         'dterm_notch_cutoff':'',
                         'debug_mode':'',
                         'd_min':'',
                         'd_min_gain':'',
                         'd_min_advance':'',
                         'feedforward_weight':'',
                         'feedforward_transition':''
                         }
            ### different versions of fw have different names for the same thing.
            translate_dic={'dynThrPID':'dynThrottle',
                         'Craft name':'craftName',
                         'Firmware type':'fwType',
                         'Firmware revision':'version',
                         'Firmware date':'date',
                         'rcRate':'rcRate', 'rc_rate':'rcRate', 'rc_rates':'rcRate',
                         'rcExpo':'rcExpo', 'rc_expo':'rcExpo',
                         'rates':'rates',
                         'rollPID':'rollPID',
                         'pitchPID':'pitchPID',
                         'yawPID':'yawPID',
                         'deadband':'deadBand',
                         'yaw_deadband':'yawDeadBand',
                         'tpa_breakpoint':'tpa_breakpoint',
                         'minthrottle':'minThrottle',
                         'maxthrottle':'maxThrottle',
                         'tpa_percent':'tpa_percent', 'tpa_rate':'tpa_percent',
                         'feedforward_weight':'feedforward_weight',
                         'vbat_pid_compensation':'vbatComp','vbat_pid_gain':'vbatComp',
                         'gyro_lpf':'gyro_lpf', 'gyro_hardware_lpf':'gyro_lpf',
                         'gyro_lowpass_type':'gyro_lowpass_type',
                         'gyro_lowpass_hz':'gyro_lowpass_hz','gyro_lpf_hz':'gyro_lowpass_hz',
                         'gyro_notch_hz':'gyro_notch_hz',
                         'gyro_notch_cutoff':'gyro_notch_cutoff',
                         'dterm_filter_type':'dterm_filter_type',
                         'dterm_lpf_hz':'dterm_lpf_hz', 'dterm_lowpass_hz':'dterm_lpf_hz',
                         'yaw_lpf_hz':'yaw_lpf_hz', 'yaw_lowpass_hz':'yaw_lpf_hz',
                         'dterm_notch_hz':'dterm_notch_hz',
                         'dterm_notch_cutoff':'dterm_notch_cutoff',
                         'debug_mode':'debug_mode',
                         'd_min':'d_min',
                         'd_min_gain':'d_min_gain',
                         'd_min_advance':'d_min_advance',
                         'feedforward_weight':'feedforward_weight',
                         'feedforward_transition':'feedforward_transition'
                         }

            headsdict['tempFile'] = bblog[0]
            headsdict['logNum'] = str(i)
            ### check for known keys and translate to useful ones.
            for l in bblog[1]:
                if l in translate_dic:
                    headsdict.update({translate_dic[l]: bblog[1][l]})
            heads.append(headsdict)
        return heads

    def decode(self, fpath):
        """Splits out one BBL per recorded session and converts each to CSV."""
        with open(fpath, 'rb') as binary_log_view:
            content = binary_log_view.read()

        # The first line of the overall BBL file re-appears at the beginning
        # of each recorded session.
        try:
          first_newline_index = content.index(str('\n').encode('utf8'))
        except ValueError as e:
            raise ValueError(
                'No newline in %dB of log data from %r.'
                % (len(content), fpath),
                e)
        firstline = content[:first_newline_index + 1]

        split = content.split(firstline)
        bbl_sessions = []
        for i in range(len(split)):
            path_root, path_ext = os.path.splitext(os.path.basename(fpath))
            temp_path = os.path.join(
                self.tmp_dir, '%s_temp%d%s' % (path_root, i, path_ext))
            with open(temp_path, 'wb') as newfile:
                newfile.write(firstline+split[i])
            bbl_sessions.append(temp_path)

        loglist = []
        for bbl_session in bbl_sessions:
            size_bytes = os.path.getsize(os.path.join(self.tmp_dir, bbl_session))
            if size_bytes > LOG_MIN_BYTES:
                try:
                    # Read header in a dictionary
                    parser = Parser.load(bbl_session)
                    headers = parser.headers
                    fields_name = parser.field_names[:42]

                    # Read data with Orangebox into A Pandas Object
                    data = []
                    for frame in parser.frames():
                        if frame.type != FrameType.GPS:
                            data.append(frame.data[:42])
                    df = pd.DataFrame(data, columns=fields_name)
                    loglist.append([bbl_session, headers, df])
                except:
                    logging.error(
                        'Error in Orangebox_decode of %r' % bbl_session, exc_info=True)
            else:
                # There is often a small bogus session at the start of the file.
                logging.warning(
                    'Ignoring BBL session %r, %dB < %dB.'
                    % (bbl_session, size_bytes, LOG_MIN_BYTES))
                os.remove(bbl_session)
        return loglist
