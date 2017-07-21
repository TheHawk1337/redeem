import unittest
import mock
import os
import sys
sys.path.insert(0, '../redeem')
# sys.path.insert(0, './gcode/TestStubs')

sys.modules['EndStop'] = mock.Mock()
sys.modules['RotaryEncoder'] = mock.Mock()
sys.modules['Watchdog'] = mock.Mock()
sys.modules['GPIO'] = mock.Mock()
sys.modules['Enable'] = mock.Mock()
sys.modules['Key_pin'] = mock.Mock()
sys.modules['GPIO'] = mock.Mock()
sys.modules['DAC'] = mock.Mock()
sys.modules['ShiftRegister.py'] = mock.Mock()
sys.modules['Adafruit_BBIO'] = mock.Mock()
sys.modules['Adafruit_BBIO.GPIO'] = mock.Mock()
sys.modules['StepperWatchdog'] = mock.Mock()
sys.modules['StepperWatchdog.GPIO'] = mock.Mock()
sys.modules['_PathPlannerNative'] = mock.Mock()
sys.modules['PruInterface'] = mock.Mock()
sys.modules['PruFirmware'] = mock.Mock()
sys.modules['Extruder'] = mock.Mock()
sys.modules['HBD'] = mock.Mock()
sys.modules['RotaryEncoder'] = mock.Mock()
sys.modules['JoinableQueue'] = mock.Mock()
sys.modules['USB'] = mock.Mock()
sys.modules['Ethernet'] = mock.Mock()
sys.modules['Pipe'] = mock.Mock()

from CascadingConfigParser import CascadingConfigParser
from Redeem import *

"""
MockPrinter, in combination with the many sys.module[...] = Mock() statements
above, creates a mock Redeem instance. The mock instance has only what is
needed for our tests and does not access any BBB hardware IOs.
"""
class MockPrinter(unittest.TestCase):

    @classmethod
    @mock.patch("Redeem.CascadingConfigParser")
    def setUpClass(self, wedged_config_parser):

        """
        Override some methods in CascadingConfigParser to prevent absence of
        hardware limiting test ability
        """
        class CascadingConfigParserWedge(CascadingConfigParser):
            def parse_capes(self):
                self.replicape_revision = "0A4A" # Fake. No hardware involved in these tests (Redundant?)
                self.reach_revision = "00A0" # Fake. No hardware involved in these tests (Redundant?)

            def get_key(self):
                return "TESTING_DUMMY_KEY"
        wedged_config_parser.side_effect = CascadingConfigParserWedge

        """
        This seemed like the best way to add to or change stuff in default.cfg,
        without actually messing with the prestine file.
        """
        tmp_local_cfg = tf = open("../configs/local.cfg", "w")
        tf.write("[System]\nlog_to_file = False\n")
        tf.write("\n[Fans]\n")
        tf.close()


        self.R = Redeem(config_location="../configs")
        printer = self.printer = self.R.printer

        self.printer.path_planner = mock.MagicMock()
        self.gcodes = self.printer.processor.gcodes
        self.printer.send_message = mock.create_autospec(self.printer.send_message)

        self.printer.movement = Path.ABSOLUTE
        self.printer.feed_rate = 0.050 # m/s
        self.printer.accel = 0.050 / 60 # m/s/s

        Gcode.printer = printer
        Path.printer = printer

        """ 
        We want to ensure that printer.factor is always obeyed correctly
        For convenience, we'll set it to mm/inch and check that resulting 
        paths have the correct meter values, converted from inch input.
        """
        self.printer.factor = self.f = 25.4 # inches

        self.printer.probe_points = []

    @classmethod
    def tearDownClass(self):
        self.R = self.printer = None
        os.remove("../configs/local.cfg")
        pass

    """ directly calls a Gcode class's execute method, bypassing printer.processor.execute """
    @classmethod
    def execute_gcode(self, text):
        g = Gcode({"message": text})
        return self.printer.processor.gcodes[g.gcode].execute(g)

    @classmethod
    def full_path(self, o):
      return o.__module__ + "." + o.__class__.__name__
