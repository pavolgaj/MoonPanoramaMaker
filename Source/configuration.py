# -*- coding: utf-8; -*-
"""
Copyright (c) 2016 Rolf Hempel, rolf6419@gmx.de

This file is part of the MoonPanoramaMaker tool (MPM).
https://github.com/Rolf-Hempel/MoonPanoramaMaker

MPM is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with MPM.  If not, see <http://www.gnu.org/licenses/>.

"""

import configparser
import os.path
import sys

from PyQt5 import QtWidgets
from configuration_editor import ConfigurationEditor
from miscellaneous import Miscellaneous


class Configuration:
    """
    The Configuration class is used to manage all parameters which can be changed or set by the
    user. This includes input / output to file for persistent storage.

    """

    def __init__(self):
        """
        Initialize the configuration object.

        """

        # The version number is displayed on the MPM main GUI title line.
        self.version = "MoonPanoramaMaker 1.0.1"

        ############################################################################################
        # Switch on/off debug modes:
        #
        # Debug mode for camera emulation: In the socket client, the interface to FireCapture is
        # emulated. FireCapture does not need to be started. No videos are captured, though.
        self.camera_debug = False
        # If camera is emulated, insert a delay (in seconds) before sending the acknowledgement
        # message (to emulate exposure time).
        self.camera_debug_delay = 2.
        #
        # Debug mode for auto-alignment visualization:
        self.alignment_debug = False
        # Please note: Since the alignment_debug option uses a MatPlotLib window which interferes
        # with the tile configuration window of MoonPanoramaMaker, this debug option can only be
        # used in unit testing (i.e. using the main program in module image_shift).
        #
        # Another parameter used for alignment debugging is "align_repetition_count". If set to a
        # value > 1, several auto-alignment operations are repeated in direct succession. This way
        # errors in the auto-alignment operation can be distinguished from other alignment errors
        # that build up in between alignments. This debugging feature is independent of the
        # alignment_debug flag and is used with the full MoonPanoramaMaker software.
        self.align_repetition_count = 1
        #
        # Debug mode for ephemeris computations: Perform ephemeris computations for a fixed date and
        # time, thus switching off temporal changes of feature positions.
        self.ephemeris_debug = False
        # If ephemeris_debug is set to True, set the fixed date and time in terms of the selected
        # time zone [year, month, day, hour, minute, second].
        self.ephemeris_fixed_datetime = [2017, 10, 15, 5, 30, 0]
        ############################################################################################

        # Set internal parameters which cannot be changed by the user.

        # If multiple exposures of a tile are to be made in succession, insert a short wait time
        # in between exposures. Otherwise FireCapture might get stuck.
        self.camera_time_between_multiple_exposures = 1.

        # If camera automation is switched on, the program communicates with a plugin in the camera
        # control software FireCapture. The plugin acts as a server and listens on a fixed port
        # number.
        self.fire_capture_port_number = 9820

        # In several places polling is used to wait for an event. A short wait time is introduced
        # after each attempt to reduce CPU load. A time-out count keeps polling from continuing
        # indefinitely. When the workflow thread is initialized, the GUI thread waits for a short
        # time (in seconds) before it accesses its instance variables.
        self.polling_interval = 0.1
        self.polling_time_out_count = 200
        self.wait_for_workflow_initialization = 2.

        # The INDI telescope server uses a fixed port number for communication.
        self.indi_port_number = 7624

        # A PulseGuide operation of "calibrate_pulse_length" milliseconds is used to find out if
        # the telescope operation is mirror-reversed in RA/DE.
        self.calibrate_pulse_length = 1000.

        # Minimum length of time interval for drift computation:
        self.minimum_drift_seconds = 600.  # 10 minutes

        # Resolution (in pixels) of overlap width in still pictures for shift determination:
        self.pixels_in_overlap_width = 40  # 40 pixels

        # Parameters used in auto-alignment:
        # In auto-alignment initialization the telescope mount is moved to two locations near
        # the alignment landmark position. The image shifts are measured using camera still images
        # and compared with the expected shifts, based on the mount displacements. These
        # measurements are used to determine whether or not the camera is oriented upright /
        # upside-down or if it is mirror-inverted. if the absolute value of the shifts deviates
        # from the expected value by more than the given fraction, auto-alignment is deemed
        # unsuccessful.
        self.align_max_autoalign_error = 0.3
        # Factor by which the interval between auto-alignments is changed:
        self.align_interval_change_factor = 1.5
        # Criterion for very precise alignment:
        self.align_very_precise_factor = 4.
        # Delete alignment pictures if they are older than the given retention period (in seconds).
        self.alignment_pictures_retention_time = 43200.

        # Parameters in CLAHE image normalization:
        # Clip limit:
        self.clahe_clip_limit = 2.
        # Tile grid size:
        self.clahe_tile_grid_size = 8

        # Parameters for ORB keypoint detection:
        # WTA_K parameter:
        self.orb_wta_k = 4  # originally: 3, optimized: 4
        # Number of features:
        self.orb_nfeatures = 50
        # Edge threshold:
        self.orb_edge_threshold = 0  # originally: 30, optimized: 0
        # Patch size:
        self.orb_patch_size = 31
        # Scale factor:
        self.orb_scale_factor = 1.2
        # Number of levels:
        self.orb_n_levels = 8

        # Parameters in shift cluster detection:
        # Cluster radius in pixels:
        self.dbscan_cluster_radius = 3.
        # Minimum sample size:
        self.dbscan_minimum_sample = 5  # originally: 10, optimized: 5
        # Minimum of measurements in cluster:
        self.dbscan_minimum_in_cluster = 5  # originally: 10, optimized: 5

        # The config file for persistent parameter storage is located in the user's home
        # directory, as is the detailed MoonPanoramaMaker logfile.
        self.home = os.path.expanduser("~")
        self.config_filename = os.path.join(self.home, ".MoonPanoramaMaker.ini")
        self.protocol_filename = os.path.join(self.home, "MoonPanoramaMaker.log")

        self.file_new = not os.path.isfile(self.config_filename)
        self.file_identical = False
        self.file_compatible = False

        # If an existing config file is found, read it in.
        if not self.file_new:
            self.conf = configparser.ConfigParser()
            self.conf.read(self.config_filename)
            # Set flag to indicate that parameters were read from file.
            self.configuration_read = True
            # Check if the file is for the current MPM version, otherwise try to update it.
            # If file could not be made compatible, do not use the old config file.
            self.file_identical, self.file_compatible = self.check_for_compatibility()

        if self.file_new or not self.file_compatible:
            # Code to set standard config info. The "Hidden Parameters" are not displayed in the
            # configuration GUI. Most of them are for placing GUI windows where they had been at
            # the previous session.
            self.configuration_read = False
            self.conf = configparser.ConfigParser()
            self.conf.add_section('Hidden Parameters')
            self.conf.set('Hidden Parameters', 'version', self.version)
            self.conf.set('Hidden Parameters', 'main window x0', '350')
            self.conf.set('Hidden Parameters', 'main window y0', '50')
            self.conf.set('Hidden Parameters', 'tile window x0', '50')
            self.conf.set('Hidden Parameters', 'tile window y0', '50')

            self.conf.add_section('Geographical Position')
            self.conf.set('Geographical Position', 'longitude', '7.39720')
            self.conf.set('Geographical Position', 'latitude', '50.69190')
            self.conf.set('Geographical Position', 'elevation', '250')
            self.conf.set('Geographical Position', 'timezone', 'Europe/Berlin')

            self.conf.add_section('Camera')
            self.conf.set('Camera', 'name', 'ZWO ASI120MM-S')
            self.conf.set('Camera', 'ip address', 'localhost')

            self.conf.add_section('Telescope')
            self.conf.set('Telescope', 'focal length', '2800.')
            self.conf.set('Telescope', 'interface type', 'ASCOM')

            self.conf.add_section('Tile Visualization')
            self.conf.set('Tile Visualization', 'figsize horizontal', '7.')
            self.conf.set('Tile Visualization', 'figsize vertical', '7.')
            self.conf.set('Tile Visualization', 'label fontsize', '9')
            self.conf.set('Tile Visualization', 'label shift', '0.8')

            self.conf.add_section('Workflow')
            self.conf.set('Workflow', 'protocol level', '2')
            self.conf.set('Workflow', 'protocol to file', 'True')
            self.conf.set('Workflow', 'camera automation', 'False')
            self.conf.set('Workflow', 'focus on star', 'False')
            self.conf.set('Workflow', 'limb first', 'False')
            self.conf.set('Workflow', 'camera trigger delay', '3.')

            self.conf.add_section('ASCOM')
            self.conf.set('ASCOM', 'telescope driver', 'POTH.Telescope')
            self.conf.set('ASCOM', 'guiding interval', '0.2')
            self.conf.set('ASCOM', 'wait interval', '1.')
            self.conf.set('ASCOM', 'pulse guide speed RA', '0.003')
            self.conf.set('ASCOM', 'pulse guide speed DE', '0.003')
            self.conf.set('ASCOM', 'telescope lookup precision', '0.5')

            self.conf.add_section('INDI')
            self.conf.set('INDI', 'web browser path', '/usr/bin/firefox')
            self.conf.set('INDI', 'server url', 'localhost')
            self.conf.set('INDI', 'guiding interval', '1.5')
            self.conf.set('INDI', 'wait interval', '2.')
            self.conf.set('INDI', 'pulse guide speed index', '0')
            self.conf.set('INDI', 'telescope lookup precision', '0.7')

            self.conf.add_section('Alignment')
            self.conf.set('Alignment', 'min autoalign interval', '30.')
            self.conf.set('Alignment', 'max autoalign interval', '180.')
            self.conf.set('Alignment', 'max alignment error', '50.')

            self.conf.add_section('Camera ZWO ASI120MM-S')
            self.conf.set('Camera ZWO ASI120MM-S', 'name', 'ZWO ASI120MM-S')
            self.conf.set('Camera ZWO ASI120MM-S', 'pixel size', '0.00375')
            self.conf.set('Camera ZWO ASI120MM-S', 'pixel horizontal', '1280')
            self.conf.set('Camera ZWO ASI120MM-S', 'pixel vertical', '960')
            self.conf.set('Camera ZWO ASI120MM-S', 'repetition count', '1')
            self.conf.set('Camera ZWO ASI120MM-S', 'external margin pixel', '300')
            self.conf.set('Camera ZWO ASI120MM-S', 'tile overlap pixel', '200')

            self.conf.add_section('Camera ZWO ASI174MC')
            self.conf.set('Camera ZWO ASI174MC', 'name', 'ZWO ASI174MC')
            self.conf.set('Camera ZWO ASI174MC', 'pixel size', '0.00586')
            self.conf.set('Camera ZWO ASI174MC', 'pixel horizontal', '1936')
            self.conf.set('Camera ZWO ASI174MC', 'pixel vertical', '1216')
            self.conf.set('Camera ZWO ASI174MC', 'repetition count', '1')
            self.conf.set('Camera ZWO ASI174MC', 'external margin pixel', '200')
            self.conf.set('Camera ZWO ASI174MC', 'tile overlap pixel', '100')

            self.conf.add_section('Camera ZWO ASI178MC')
            self.conf.set('Camera ZWO ASI178MC', 'name', 'ZWO ASI178MC')
            self.conf.set('Camera ZWO ASI178MC', 'pixel size', '0.0024')
            self.conf.set('Camera ZWO ASI178MC', 'pixel horizontal', '3096')
            self.conf.set('Camera ZWO ASI178MC', 'pixel vertical', '2080')
            self.conf.set('Camera ZWO ASI178MC', 'repetition count', '1')
            self.conf.set('Camera ZWO ASI178MC', 'external margin pixel', '550')
            self.conf.set('Camera ZWO ASI178MC', 'tile overlap pixel', '250')

            self.conf.add_section('Camera ZWO ASI185MC')
            self.conf.set('Camera ZWO ASI185MC', 'name', 'ZWO ASI185MC')
            self.conf.set('Camera ZWO ASI185MC', 'pixel size', '0.00375')
            self.conf.set('Camera ZWO ASI185MC', 'pixel horizontal', '1944')
            self.conf.set('Camera ZWO ASI185MC', 'pixel vertical', '1224')
            self.conf.set('Camera ZWO ASI185MC', 'repetition count', '1')
            self.conf.set('Camera ZWO ASI185MC', 'external margin pixel', '300')
            self.conf.set('Camera ZWO ASI185MC', 'tile overlap pixel', '150')

            self.conf.add_section('Camera ZWO ASI224MC')
            self.conf.set('Camera ZWO ASI224MC', 'name', 'ZWO ASI224MC')
            self.conf.set('Camera ZWO ASI224MC', 'pixel size', '0.00375')
            self.conf.set('Camera ZWO ASI224MC', 'pixel horizontal', '1304')
            self.conf.set('Camera ZWO ASI224MC', 'pixel vertical', '976')
            self.conf.set('Camera ZWO ASI224MC', 'repetition count', '1')
            self.conf.set('Camera ZWO ASI224MC', 'external margin pixel', '300')
            self.conf.set('Camera ZWO ASI224MC', 'tile overlap pixel', '150')

            self.conf.add_section('Camera Celestron Skyris 274C')
            self.conf.set('Camera Celestron Skyris 274C', 'name', 'Celestron Skyris 274C')
            self.conf.set('Camera Celestron Skyris 274C', 'pixel size', '0.0044')
            self.conf.set('Camera Celestron Skyris 274C', 'pixel horizontal', '1600')
            self.conf.set('Camera Celestron Skyris 274C', 'pixel vertical', '1200')
            self.conf.set('Camera Celestron Skyris 274C', 'repetition count', '1')
            self.conf.set('Camera Celestron Skyris 274C', 'external margin pixel', '250')
            self.conf.set('Camera Celestron Skyris 274C', 'tile overlap pixel', '150')

            self.conf.add_section('Camera Celestron Skyris 445M')
            self.conf.set('Camera Celestron Skyris 445M', 'name', 'Celestron Skyris 445M')
            self.conf.set('Camera Celestron Skyris 445M', 'pixel size', '0.00375')
            self.conf.set('Camera Celestron Skyris 445M', 'pixel horizontal', '1280')
            self.conf.set('Camera Celestron Skyris 445M', 'pixel vertical', '960')
            self.conf.set('Camera Celestron Skyris 445M', 'repetition count', '1')
            self.conf.set('Camera Celestron Skyris 445M', 'external margin pixel', '300')
            self.conf.set('Camera Celestron Skyris 445M', 'tile overlap pixel', '150')

            self.conf.add_section('Camera Celestron Skyris 618M')
            self.conf.set('Camera Celestron Skyris 618M', 'name', 'Celestron Skyris 618M')
            self.conf.set('Camera Celestron Skyris 618M', 'pixel size', '0.0056')
            self.conf.set('Camera Celestron Skyris 618M', 'pixel horizontal', '640')
            self.conf.set('Camera Celestron Skyris 618M', 'pixel vertical', '480')
            self.conf.set('Camera Celestron Skyris 618M', 'repetition count', '1')
            self.conf.set('Camera Celestron Skyris 618M', 'external margin pixel', '200')
            self.conf.set('Camera Celestron Skyris 618M', 'tile overlap pixel', '100')

            # Fill the entries of section "Camera" by copying the entries from the chosen
            # camera model.
            self.copy_camera_configuration(self.conf.get('Camera', 'name'))

        # Initialize instance variables.
        self.old_versions = None
        self.protocol_level = None
        self.section_name = None

        # Set the "protocol_level" variable. This will control the amount of protocol output.
        self.set_protocol_level()

    def set_parameter(self, section, name, value):
        """
        Assign a new value to a parameter in the configuration object. The value is not checked for
        validity. Therefore, this method should be used with well-defined values internally only.

        :param section: section name (e.g. 'Workflow') within the JSON data object
        :param name: name of the parameter (e.g. 'protocol level')
        :param value: new value to be assigned to the parameter (type str)
        :return: True, if the parameter was assigned successfully. False, otherwise.
        """

        try:
            self.conf.set(section, name, value)
            return True
        except:
            return False

    def check_for_compatibility(self):
        """
        Test if the MoonPanoramaMaker version number in the parameter file read differs from the
        current version. If so, change / add parameters to make them compatible with the current
        version. At program termination the new parameter set will be written, so next time the
        parameters will be consistent.

        :return: (file_identical, file_compatible), where:
                  file_identical: True if the data was imported from a file with the same format
                                  as the current one. False, if the format was different.
                  file_compatible: True if the file read has the same format as the current version,
                                   or the data read from the file could be made compatible with the
                                   current version. Otherwise return False.
        """

        # Old versions for which configuration file import is supported.
        self.old_versions = ["MoonPanoramaMaker 0.9.3", "MoonPanoramaMaker 0.9.5", "MoonPanoramaMaker 1.0.0"]

        version_read = self.conf.get('Hidden Parameters', 'version')
        if version_read == self.version:
            # Configuration file matches current format. Nothing to be done.
            file_identical = True
            file_compatible = True

        elif version_read not in self.old_versions:
            # Parameter file cannot be imported.
            file_identical = False
            file_compatible = False

        else:
            # File can be imported. Conversions are necessary, possibly in several steps.
            if self.old_versions.index(version_read) == 0:
                # Changes for file version 0.9.3:
                #
                # The handling of session protocol has changed.
                wp = self.conf.getboolean('Workflow', 'protocol')
                if wp:
                    self.conf.set('Workflow', 'protocol level', '2')
                else:
                    self.conf.set('Workflow', 'protocol level', '0')
                self.conf.remove_option('Workflow', 'protocol')
                # Add the parameter "focus on star" which was introduced with version 0.9.5.
                self.conf.set('Workflow', 'focus on star', 'False')
                # Add the "Alignment" section which was introduced with version 0.9.5.
                self.conf.add_section('Alignment')
                self.conf.set('Alignment', 'min autoalign interval', '30.')
                self.conf.set('Alignment', 'max autoalign interval', '300.')
                self.conf.set('Alignment', 'max alignment error', '50.')
                # Set the repetition count parameter for each camera. This camera parameter was
                # introduced with version 0.9.5., too. The parameter is in section "Camera" as well
                # as in all parameter sets of supported camera models.
                self.conf.set('Camera', 'repetition count', '1')
                for cam in self.get_camera_list():
                    self.conf.set('Camera ' + cam, 'repetition count', '1')

            if self.old_versions.index(version_read) <= 1:
                # Changes for file version 0.9.5 or earlier:
                #
                # The ASCOM telescope driver was selected via a chooser GUI. Now the name of the
                # ASCOM driver is given by a configuration parameter. Take the name of the ASCOM
                # telescope hub for the telescope driver and remove the old configuration
                # parameter names.
                self.conf.set('Telescope', 'interface type', 'ASCOM')
                self.conf.set('ASCOM', 'telescope driver', self.conf.get('ASCOM', 'hub'))
                self.conf.set('ASCOM', 'pulse guide speed RA', '0.003')
                self.conf.set('ASCOM', 'pulse guide speed DE', '0.003')
                self.conf.remove_option('ASCOM', 'chooser')
                self.conf.remove_option('ASCOM', 'hub')
                # A new section "INDI" was added for telescope control under Linux.
                self.conf.add_section('INDI')
                self.conf.set('INDI', 'web browser path', '/usr/bin/firefox')
                self.conf.set('INDI', 'server url', 'localhost')
                self.conf.set('INDI', 'guiding interval', '1.5')
                self.conf.set('INDI', 'wait interval', '2.')
                self.conf.set('INDI', 'pulse guide speed index', '0')
                self.conf.set('INDI', 'telescope lookup precision', '0.7')
                # FireCapture may run on a differenct computer now. Specify its IP address.
                self.conf.set('Camera', 'ip address', 'localhost')

                scale = 7. / 8.5
                new_figsize_horizontal = round(
                    self.conf.getfloat('Tile Visualization', 'figsize horizontal') * scale, 1)
                self.conf.set('Tile Visualization', 'figsize horizontal',
                              str(new_figsize_horizontal))
                new_figsize_vertical = round(
                    self.conf.getfloat('Tile Visualization', 'figsize vertical') * scale, 1)
                self.conf.set('Tile Visualization', 'figsize vertical', str(new_figsize_vertical))
                new_label_fontsize = int(
                    self.conf.getfloat('Tile Visualization', 'label fontsize') * scale)
                self.conf.set('Tile Visualization', 'label fontsize', str(new_label_fontsize))

            if self.old_versions.index(version_read) <= 2:
                # Changes for file version 1.0.0 or earlier:
                #
                # Configuration files are identical for versions 1.0.0 and 1.0.1.
                pass

            # The configuration file could be imported, but the contents may not be up to date.
            file_identical = False
            file_compatible = True
            # Update the version number.
            self.conf.set('Hidden Parameters', 'version', self.version)

        return file_identical, file_compatible

    def set_protocol_level(self):
        """
        Read from the configuration object the level of detail for the session protocol. The
        follwoing levels are supported:
        0:  No session protocol
        1:  Minimal protocol, only high-level activities, e.g. alignments, video aquisitions,
            no details
        2:  Quantitative information on high-level activities
        3:  Detailed information also on low-level activities (only for debugging)

        :return: -
        """

        self.protocol_level = self.conf.getint('Workflow', 'protocol level')

    def get_camera_list(self):
        """
        Look up all camera models, for which parameters are stored in the configuration object.

        :return: list of all available camera names (strings)
        """

        return [name[7:] for name in self.conf.sections() if name[:7] == 'Camera ']

    def copy_camera_configuration(self, name):
        """
        Copy the parameters stored for a given camera model into the section "Camera" of the
        configuration object. The parameters in this section are used by MoonPanoramaMaker's
        computations.

        :param name: Name (string) of the selected camera model
        :return: -
        """

        self.section_name = 'Camera ' + name
        self.conf.set('Camera', 'name', self.conf.get(self.section_name, 'name'))
        self.conf.set('Camera', 'pixel size', self.conf.get(self.section_name, 'pixel size'))
        self.conf.set('Camera', 'pixel horizontal',
                      self.conf.get(self.section_name, 'pixel horizontal'))
        self.conf.set('Camera', 'pixel vertical',
                      self.conf.get(self.section_name, 'pixel vertical'))
        self.conf.set('Camera', 'repetition count',
                      self.conf.get(self.section_name, 'repetition count'))
        self.conf.set('Camera', 'external margin pixel',
                      self.conf.get(self.section_name, 'external margin pixel'))
        self.conf.set('Camera', 'tile overlap pixel',
                      self.conf.get(self.section_name, 'tile overlap pixel'))

    def write_config(self):
        """
        Write the contentes of the configuration object back to the configuration file in the
        user's home directory.

        :return: -
        """

        with open(self.config_filename, 'w') as config_file:
            self.conf.write(config_file)


if __name__ == "__main__":
    c = Configuration()
    camera_list = c.get_camera_list()
    app = QtWidgets.QApplication(sys.argv)
    initialized = True
    editor = ConfigurationEditor(c, initialized)
    editor.show()
    app.exec_()

    print("Current version: ", c.version)
    print("Configuration read from file: " + str(c.configuration_read))
    print("File identical: " + str(c.file_identical))
    print("File compatible: " + str(c.file_compatible))

    if editor.output_channel_changed:
        print("Output channel changed.")
    print("Protocol level: " + str(c.protocol_level))
    if editor.telescope_changed:
        print("Telescope changed.")
    if editor.camera_automation_changed:
        print("Camera automation changed.")
    if editor.tesselation_changed:
        print("Tesselation changed.")
    if editor.configuration_changed or not c.configuration_read:
        print("Configuration has changed, write back config file. ")
        c.write_config()

    print("Setting protocol level to '2'. Success: " +
           str(c.set_parameter('Workflow', 'protocol level', '2')))
    c.write_config()
