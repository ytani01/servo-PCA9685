#!/usr/bin/env python3
#
# (c) 2020 FabLab Kannai
#
"""
Rotation Motor driver for Music Box

Usage
-----
servo = MusicBoxServo()
 :
servo.tap([0, 3, 7])  # list of channel numbers
 :
servo.end()
-----
"""
__author__ = 'FabLab Kannai'
__date__   = '2020/12'

from ServoPCA9685 import ServoPCA9685
import pigpio
import time
from MyLogger import get_logger


class MusicBoxServo:
    """オルゴール用サーボモーター
    """
    _log = get_logger(__name__, False)

    DEF_CONF_FNAME = "music-box-servo.conf"
    DEF_CONF_DIR   = "/home/pi"
    DEF_CONFFILE   = DEF_CONF_DIR + '/' + DEF_CONF_FNAME

    DEF_ON_INTERVAL  = 1.5  # sec
    DEF_OFF_INTERVAL = 0.5  # sec

    SERVO_N        = 15

    VAL_CENTER     = 1500

    ON_CHR         = 'oO*'

    def __init__(self, conf_file=DEF_CONFFILE,
                 on_interval=DEF_ON_INTERVAL,
                 off_interval=DEF_OFF_INTERVAL,
                 debug=False):
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('conf_file=%s' % conf_file)
        self._log.debug('on_interval=%s, off_interval=%s',
                        on_interval, off_interval)

        self.conf_file = conf_file
        self.on_interval = on_interval
        self.off_interval = off_interval

        self.pi = pigpio.pi()

        self.on = [self.VAL_CENTER] * self.SERVO_N
        self.off = [self.VAL_CENTER] * self.SERVO_N
        self._log.debug('on=%s', self.on)
        self._log.debug('off=%s', self.off)

        self.load_conf(self.conf_file)

        self.servo = ServoPCA9685(self.pi, list(range(self.SERVO_N)),
                                  debug=self._dbg)
        self.pull()

    def end(self):
        """終了処理

        プログラム終了時に呼ぶこと
        """
        self._log.debug('doing ..')
        self.servo.end()
        self.pi.stop()
        self._log.debug('done')

    def load_conf(self, conf_file=None):
        """設定ファイルを読み込む

        Parameters
        ----------
        conf_file: str
            設定ファイル名(フルパス)
        """
        self._log.debug('conf_file=%s', conf_file)

        if conf_file is None:
            conf_file = self.conf_file
            self._log.debug('conf_file=%s', conf_file)

        with open(conf_file) as f:
            lines = f.readlines()

        for line in lines:
            col = line.replace(' ', '').rstrip('\n').split(',')
            self._log.debug('col=%s', col)

            if len(col) != 3:
                continue

            if col[0][0] == '#':
                continue

            [ch, on, off] = [int(s) for s in col]

            self.on[ch] = on
            self.off[ch] = off

        self._log.debug('on=%s', self.on)
        self._log.debug('off=%s', self.off)

    def holestr2chlist(self, hole):
        """穴の位置を示した文字列をONにするチャンネル・リストに変換

        self.ON_CHRに含まれる文字を「ON」、それ以外を「OFF」と見なす。

        ex.
        '---o-o-o------'
        '----O-*-o-----'

        Parameters
        ----------
        hole: str
            穴の位置を示した文字列: ex. '--o-o-o----------'

        Returns
        -------
        ch_list: list of int
            ONにするチャンネル番号のリスト
        """
        self._log.debug('hole=%s', hole)

        ch_list = []
        for i, c1 in enumerate(hole):
            if c1 in self.ON_CHR:
                ch_list.append(i)

        self._log.debug('ch_list=%s', ch_list)
        return ch_list

    def tap(self, ch):
        """指定されたチャンネルのピン(複数)を弾く

        Parameters
        ----------
        ch: list of str
            チャンネル番号: 0..15
        """
        self._log.debug('ch=%s', ch)

        self.push(ch)
        time.sleep(self.on_interval)
        self.pull()
        time.sleep(self.off_interval)

    def push(self, ch):
        """指定されたチャンネルのピンを押す

        Parameters
        ----------
        ch: int
            チャンネル番号: 0..15
        """
        self._log.debug('ch=%s', ch)
        for c in ch:
            if c < 0 or c >= self.SERVO_N:
                raise ValueError('invalid channel number. specify 0..15')

        on_list = [self.on[c] for c in ch]
        self._log.debug('on_list=%s', on_list)

        pwm = [0] * self.SERVO_N
        for c in range(self.SERVO_N):
            pwm[c] = self.off[c]
            if c in ch:
                pwm[c] = self.on[c]

        self._log.debug('pwm=%s', pwm)
        self.servo.set_pwm(pwm)

    def pull(self):
        """全チャンネルのピンを引く
        """
        self._log.debug('')
        self.servo.set_pwm(self.off)


""" 以下、サンプル・コード """


class Sample:
    """サンプル
    """
    _log = get_logger(__name__, False)

    def __init__(self, conf_file, on_interval, off_interval,
                 debug=False):
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('conf_file=%s', conf_file)
        self._log.debug('on_interval=%s, off_interaval=%s',
                        on_interval, off_interval)

        self.servo = MusicBoxServo(conf_file, on_interval, off_interval,
                                   debug=self._dbg)

    def main(self):
        self._log.debug('')

        while True:
            prompt = '[0-15, ..]> '
            try:
                line1 = input(prompt)
            except Exception as e:
                self._log.error('%s:%s', type(e), e)
                continue
            self._log.debug('line1=%a', line1)

            if len(line1) == 0:
                # end
                break

            ch_str = line1.replace(' ', '').split(',')
            self._log.debug('ch_str=%s', ch_str)

            if ch_str[0].startswith('!'):
                ch_str = ch_str[0].strip('!')
                ch = self.servo.holestr2chlist(ch_str)
            else:
                try:
                    ch = [int(s) for s in ch_str]
                except Exception as e:
                    self._log.error('%s: %s', type(e), e)
                    continue

            self._log.debug('ch=%s', ch)

            self.servo.tap(ch)

    def end(self):
        self._log.debug('')
        self.servo.end()


import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS, help="""
MusicBoxServo class test program
""")
@click.option('--conf', '-f', '-c', 'conf_file',
              type=click.Path(exists=True),
              default=MusicBoxServo.DEF_CONFFILE,
              help='configuration file')
@click.option('--on_interval', '-o', 'on_interval', type=float,
              default=MusicBoxServo.DEF_ON_INTERVAL,
              help='on interval[sec]')
@click.option('--off_interval', '-O', 'off_interval', type=float,
              default=MusicBoxServo.DEF_OFF_INTERVAL,
              help='off interval[sec]')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(conf_file, on_interval, off_interval, debug):
    """サンプル起動用メイン関数
    """
    log = get_logger(__name__, debug)
    log.debug('conf_file=%s', conf_file)
    log.debug('on_interval=%s, off_interval=%s',
              on_interval, off_interval)

    app = Sample(conf_file, on_interval, off_interval, debug=debug)

    try:
        app.main()
    finally:
        log.debug('finally')
        app.end()
        log.info('end')


if __name__ == '__main__':
    main()