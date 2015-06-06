# -*- coding: utf-8 -*-
"""
/***************************************************************************
 swathProfile
                                 A QGIS plugin
 This plugin creates profiles along a baseline
                             -------------------
        begin                : 2015-06-04
        copyright            : (C) 2015 by Maximilian Krambach
        email                : maximilian.krambach@gmx.de
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load swathProfile class from file swathProfile.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .swath_profile import swathProfile
    return swathProfile(iface)
