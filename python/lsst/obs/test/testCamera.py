# This file is part of obs_test.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import numpy as np

import lsst.afw.cameraGeom as cameraGeom
import lsst.afw.geom as afwGeom
from lsst.afw.table import AmpInfoCatalog, AmpInfoTable, LL
from lsst.afw.cameraGeom import NullLinearityType
from lsst.afw.cameraGeom.cameraFactory import makeDetector

__all__ = ["TestCamera"]


class TestCamera(cameraGeom.Camera):
    """A simple test Camera

    There is one ccd with name "0"
    It has four amplifiers with names "00", "01", "10", and "11"

    The camera is modeled after a small portion of the LSST sim Summer 2012 camera:
    a single detector with four amplifiers, consisting of
    raft 2,2 sensor 0,0, half of channels 0,0 0,1 1,0 and 1,1 (the half closest to the Y centerline)

    Note that the Summer 2012 camera has one very weird feature: the bias region
    (rawHOverscanBbox) is actually a prescan (appears before the data pixels).

    A raw image has the sky in the same orientation on all amplifier subregions,
    so no amplifier subregions need their pixels to be flipped.

    Standard keys are:
    amp: amplifier number: one of 00, 01, 10, 11
    ccd: ccd number: always 0
    visit: exposure number; test data includes one exposure with visit=1
    """

    def __init__(self):
        """Construct a TestCamera
        """
        plateScale = afwGeom.Angle(20, afwGeom.arcseconds)  # plate scale, in angle on sky/mm
        # Radial distortion is modeled as a radial polynomial that converts from focal plane (in mm)
        # to field angle (in radians). Thus the coefficients are:
        # C0: always 0, for continuity at the center of the focal plane; units are rad
        # C1: 1/plateScale; units are rad/mm
        # C2: usually 0; units are rad/mm^2
        # C3: radial distortion; units are rad/mm^3
        radialCoeff = np.array([0.0, 1.0, 0.0, 0.925]) / plateScale.asRadians()
        fieldAngleToFocalPlane = afwGeom.makeRadialTransform(radialCoeff)
        focalPlaneToFieldAngle = fieldAngleToFocalPlane.getInverse()
        cameraTransformMap = cameraGeom.TransformMap(cameraGeom.FOCAL_PLANE,
                                                     {cameraGeom.FIELD_ANGLE: focalPlaneToFieldAngle})
        detectorList = self._makeDetectorList(focalPlaneToFieldAngle)
        cameraGeom.Camera.__init__(self, "test", detectorList, cameraTransformMap)

    def _makeDetectorList(self, focalPlaneToFieldAngle):
        """Make a list of detectors

        @param[in] focalPlaneToFieldAngle  An lsst.afw.geom.TransformPoint2ToPoint2
            that transforms from FOCAL_PLANE to FIELD_ANGLE coordinates
            in the forward direction
        @return a list of detectors (lsst.afw.cameraGeom.Detector)
        """
        detectorList = []
        detectorConfigList = self._makeDetectorConfigList()
        for detectorConfig in detectorConfigList:
            ampInfoCatalog = self._makeAmpInfoCatalog()
            detector = makeDetector(detectorConfig, ampInfoCatalog, focalPlaneToFieldAngle)
            detectorList.append(detector)
        return detectorList

    def _makeDetectorConfigList(self):
        """Make a list of detector configs

        @return a list of detector configs (lsst.afw.cameraGeom.DetectorConfig)
        """
        # this camera has one detector that corresponds to a subregion of lsstSim detector R:2,2 S:0,0
        # with lower left corner 0, 1000 and dimensions 1018 x 2000
        # i.e. half of each of the following channels: 0,0, 0,1, 1,0 and 1,1
        detector0Config = cameraGeom.DetectorConfig()
        detector0Config.name = '0'
        detector0Config.id = 0
        detector0Config.serial = '0000011'
        detector0Config.detectorType = 0
        detector0Config.bbox_x0 = 0
        detector0Config.bbox_x1 = 1017
        detector0Config.bbox_y0 = 0
        detector0Config.bbox_y1 = 1999
        detector0Config.pixelSize_x = 0.01
        detector0Config.pixelSize_y = 0.01
        detector0Config.transformDict.nativeSys = 'Pixels'
        detector0Config.transformDict.transforms = None
        detector0Config.refpos_x = 2035.5
        detector0Config.refpos_y = 999.5
        detector0Config.offset_x = -42.26073
        detector0Config.offset_y = -42.21914
        detector0Config.transposeDetector = False
        detector0Config.pitchDeg = 0.0
        detector0Config.yawDeg = 90.0
        detector0Config.rollDeg = 0.0
        return [detector0Config]

    def _makeAmpInfoCatalog(self):
        """Construct an amplifier info catalog

        The LSSTSim S12 amplifiers are unusual in that they start with 4 pixels
        of usable bias region (which is used to set rawHOverscanBbox, despite the name),
        followed by the data. There is no other underscan or overscan.
        """
        xDataExtent = 509  # trimmed
        yDataExtent = 1000
        xBiasExtent = 4
        xRawExtent = xDataExtent + xBiasExtent
        yRawExtent = yDataExtent
        readNoise = 3.975  # amplifier read noise, in e-
        saturationLevel = 65535
        linearityType = NullLinearityType
        linearityCoeffs = [0, 0, 0, 0]

        schema = AmpInfoTable.makeMinimalSchema()

        self.ampInfoDict = {}
        ampCatalog = AmpInfoCatalog(schema)
        for ampX in (0, 1):
            for ampY in (0, 1):
                # amplifier gain (e-/ADU) and read noiuse (ADU/pixel) from lsstSim raw data
                # note that obs_test amp <ampX><ampY> = lsstSim amp C<ampY>,<ampX> (axes are swapped)
                gain = {
                    (0, 0): 1.7741,     # C0,0
                    (0, 1): 1.65881,    # C1,0
                    (1, 0): 1.74151,    # C0,1
                    (1, 1): 1.67073,    # C1,1
                }[(ampX, ampY)]
                readNoise = {
                    (0, 0): 3.97531706217237,   # C0,0
                    (0, 1): 4.08263755342685,   # C1,0
                    (1, 0): 4.02753931932633,   # C0,1
                    (1, 1): 4.1890610691135,    # C1,1
                }[(ampX, ampY)]
                record = ampCatalog.addNew()
                record.setName("%d%d" % (ampX, ampY))
                record.setBBox(afwGeom.Box2I(
                    afwGeom.Point2I(ampX * xDataExtent, ampY * yDataExtent),
                    afwGeom.Extent2I(xDataExtent, yDataExtent),
                ))

                x0Raw = ampX * xRawExtent
                y0Raw = ampY * yRawExtent

                # bias region (which is prescan, in this case) is before the data
                readCorner = LL
                x0Bias = x0Raw
                x0Data = x0Bias + xBiasExtent

                record.setRawBBox(afwGeom.Box2I(
                    afwGeom.Point2I(x0Raw, y0Raw),
                    afwGeom.Extent2I(xRawExtent, yRawExtent),
                ))
                record.setRawDataBBox(afwGeom.Box2I(
                    afwGeom.Point2I(x0Data, y0Raw),
                    afwGeom.Extent2I(xDataExtent, yDataExtent),
                ))
                record.setRawHorizontalOverscanBBox(afwGeom.Box2I(
                    afwGeom.Point2I(x0Bias, y0Raw),
                    afwGeom.Extent2I(xBiasExtent, yRawExtent),
                ))
                record.setRawXYOffset(afwGeom.Extent2I(x0Raw, y0Raw))
                record.setReadoutCorner(readCorner)
                record.setGain(gain)
                record.setReadNoise(readNoise)
                record.setSaturation(saturationLevel)
                record.setSuspectLevel(float("nan"))
                record.setLinearityCoeffs([float(val) for val in linearityCoeffs])
                record.setLinearityType(linearityType)
                record.setHasRawInfo(True)
                record.setRawFlipX(False)
                record.setRawFlipY(False)
                record.setRawVerticalOverscanBBox(afwGeom.Box2I())  # no vertical overscan
                record.setRawPrescanBBox(afwGeom.Box2I())  # no horizontal prescan
        return ampCatalog
