#
# SPDX-License-Identifier: MIT
#

from oeqa.runtime.case import OERuntimeTestCase
from oeqa.core.decorator.depends import OETestDepends
from oeqa.core.decorator.data import skipIfNotFeature
from oeqa.runtime.decorator.package import OEHasPackage
import threading
import time

class WestonTest(OERuntimeTestCase):

    @OETestDepends(['ssh.SSHTest.test_ssh'])
    @OEHasPackage(['weston'])
    def test_weston_running(self):
        cmd ='%s | grep [w]eston-desktop-shell' % self.tc.target_cmds['ps']
        status, output = self.target.run(cmd)
        msg = ('Weston does not appear to be running %s' %
              self.target.run(self.tc.target_cmds['ps'])[1])
        self.assertEqual(status, 0, msg=msg)

    def get_weston_command(self, cmd):
        return 'export XDG_RUNTIME_DIR=/run/user/0; export DISPLAY=:0; %s' % cmd

    def run_weston_init(self):
        self.target.run(self.get_weston_command('weston'))

    def get_new_wayland_process(self, existing_wl_processes):
        try_cnt = 0
        while try_cnt < 5:
            time.sleep(5 + 5*try_cnt)
            try_cnt += 1
            status, output = self.target.run('pidof weston-desktop-shell')
            self.assertEqual(status, 0, msg='Retrieve existing and new weston-desktop-shell processes error: %s' % output)
            wl_processes = output.split(" ")
            new_wl_processes = [x for x in wl_processes if x not in existing_wl_processes]
            if new_wl_processes:
                return new_wl_processes, try_cnt

        return new_wl_processes, try_cnt

    @OEHasPackage(['weston'])
    def test_weston_info(self):
        status, output = self.target.run(self.get_weston_command('weston-info'))
        self.assertEqual(status, 0, msg='weston-info error: %s' % output)

    @OEHasPackage(['weston'])
    def test_weston_can_initialize_new_wayland_compositor(self):
        status, output = self.target.run('pidof weston-desktop-shell')
        self.assertEqual(status, 0, msg='Retrieve existing weston-desktop-shell processes error: %s' % output)
        existing_wl_processes = output.split(" ")

        weston_thread = threading.Thread(target=self.run_weston_init)
        weston_thread.start()
        new_wl_processes, try_cnt = self.get_new_wayland_process(existing_wl_processes)
        self.assertTrue(new_wl_processes, msg='Check new weston-desktop-shell processes error: %s (try_cnt:%s)' % (new_wl_processes, try_cnt))
        for wl in new_wl_processes:
            self.target.run('kill -9 %s' % wl)
