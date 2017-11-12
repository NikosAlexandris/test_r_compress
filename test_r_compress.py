"""
Name:       Tests on NULL file compression
Purpose:    Test if NULL compression preserves raster data
Source:     <https://trac.osgeo.org/grass/ticket/2750#comment:63>
@author Nikos Alexamdris
"""

"""Globals"""

GRASS_COMPRESS_NULLS_ENABLED='1'
GRASS_COMPRESS_NULLS_DISABLED='0'
WEST=637500
EAST=637600
SOUTH=221750
NORTH=221850
PRECISION = 0.0001  # for comparisons
ELEVATION = 'elevation'
MAP_WITHOUT_NULLS='map_without_NULL'
MAP_A='map_a_with_NULL'
MAP_B='map_b_with_NULL'
MAP_AB='maps_ab_with_NULL'
MESSAGE = "> Univariate statistics of <{testmap}>"

"""Librairies"""

from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule
# from grass.gunittest.gmodules import call_module

import grass.script as g
import os

"""Helper functions"""

def get_raster_univariate_statistics(raster):
    """
    """
    univar_string = g.read_command('r.univar', flags='g', map=raster)
    # message = MESSAGE.format(testmap=raster) + '\n' + univar_string
    # print message
    return univar_string

def is_null_file_compressed(raster):
    """
    Check is NULL file of a raster map is compressed
    """
    module = SimpleModule('r.compress', flags='g' , map=raster)
    module.run()
    status = module.outputs.stdout.split('|')[-1]

    # # Verbosity -------------------------------------------------
    # message = "NULL file compression for <{tm}>: ".format(tm=raster)
    # message += status
    # print message
    # # Verbosity -------------------------------------------------

    return status

def switch_grass_compress_nulls_variable(status):
    """
    Switch GRASS_COMPRESS_NULLS variable:
    - to 1 if 0
    - to 0 if 0
    """
    global MESSAGE

    if status == GRASS_COMPRESS_NULLS_DISABLED:
        os.environ['GRASS_COMPRESS_NULLS'] = GRASS_COMPRESS_NULLS_ENABLED
        message = "enabled\n\n"

    else:
        os.environ['GRASS_COMPRESS_NULLS'] = GRASS_COMPRESS_NULLS_DISABLED
        message = "disabled\n\n"

    # print "'GRASS_COMPRESS_NULLS' set to: ", message

class TestCompressIncludingNULL(TestCase):
    """
    Test Case Class

    On a raster map with NULL cells, test NULL file compression
    [GRASS_COMPRESS_NULLS=0 or GRASS_COMPRESS_NULLS=1] via

    - the result of r.compress via `r.univar -g`
    - the result of r.null -z

    On two raster maps, map A with compressed NULL cells and map B with
    uncompressed NULL cells, test the result of 'map A + map B' for both cases
    when NULL file compression is enabled and disabled.
    """

    @classmethod
    def setUpClass(cls):
        """
        Use the extent of the 'elevation' mapset as a temporary region and setup
        """
        cls.use_temp_region()
        cls.runModule('g.region', raster=ELEVATION)

    @classmethod
    def tearDownClass(cls):
        """
        Remove the temporary region
        """
        cls.del_temp_region()

    def tearDown(self):
        """
        Remove test raster maps created during and for the test
        """
        self.runModule('g.remove', flags='f', type='raster', name=MAP_WITHOUT_NULLS)
        self.runModule('g.remove', flags='f', type='raster', name=MAP_A)
        self.runModule('g.remove', flags='f', type='raster', name=MAP_B)
        self.runModule('g.remove', flags='f', type='raster', name=MAP_AB)

    def setUp(self):
        """
        Set up region and create test raster maps
        """
        # set up a small region
        self.runModule('g.region', w=WEST, e=EAST, s=SOUTH, n=NORTH)

        # create a small raster map with cells set to 1
        expression_one="{t} = 1".format(t=MAP_WITHOUT_NULLS)
        self.runModule('r.mapcalc', expression=expression_one, overwrite=True)
        is_null_file_compressed(MAP_WITHOUT_NULLS)

        # set up a larger region
        self.runModule('g.region', raster=ELEVATION)

        # derive a larger raster map A containing NULLs
        expression_two="{t} = {i}".format(t=MAP_A,
                i=MAP_WITHOUT_NULLS)
        self.runModule('r.mapcalc', expression=expression_two, overwrite=True)
        is_null_file_compressed(MAP_A)

        # derive a larger raster map B containing NULLs
        expression_two="{t} = {i}".format(t=MAP_B,
                i=MAP_WITHOUT_NULLS)
        self.runModule('r.mapcalc', expression=expression_two, overwrite=True)
        is_null_file_compressed(MAP_B)

    def test_null_file_compression_on_single_map(self):
        """
        This function tests if NULL file compression preserves the data via the
        following steps:

        - Get univariate statistics of a raster map that contains NULLs
        - Switch NULL file compression (unset if already set and vice versa)
        - Recreate the NULL file of the raster map (with or without NULL file
          compression)
        - Compare univariate statistics of the raster map (after recreation of
          the NULL file)
        """
        # is_null_file_compressed(MAP_A)
        univar_string = get_raster_univariate_statistics(MAP_A)
        switch_grass_compress_nulls_variable(os.environ['GRASS_COMPRESS_NULLS'])
        self.assertModule('r.null', flags='z', map=MAP_A, quiet=True)
        # is_null_file_compressed(MAP_A)
        # get_raster_univariate_statistics(MAP_A)
        self.assertRasterFitsUnivar(raster=MAP_A,
                precision=PRECISION, reference=univar_string)

    def test_null_file_compression_on_mapcalc_addition(self):
        """
        Further, the addition of the following maps is tested regarding NULL
        file compression:

        - map 'a' has compressed NULL file
        - map 'b' has an uncompressed NULL file

        - compute map 'ab' = 'a' + 'b'
        - get univariate statistics of map 'ab'

        - switch NULL file compression (unset if already set and vice versa)
        - recompute map 'ab' = 'a' + 'b'

        - assert univariate statistics of recomputed raster map 'ab'
        """
        # is_null_file_compressed(MAP_A)
        # is_null_file_compressed(MAP_B)

        expression_three="{ab} = {a} + {b}".format(ab=MAP_AB,
                a=MAP_A, b=MAP_B)
        self.runModule('r.mapcalc', expression=expression_three, overwrite=True)
        # is_null_file_compressed(MAP_AB)
        ab_univar_string = get_raster_univariate_statistics(MAP_AB)

        switch_grass_compress_nulls_variable(os.environ['GRASS_COMPRESS_NULLS'])

        expression_three="{ab} = {a} + {b}".format(ab=MAP_AB,
                a=MAP_A, b=MAP_B)
        self.runModule('r.mapcalc', expression=expression_three, overwrite=True)
        # is_null_file_compressed(MAP_AB)
        get_raster_univariate_statistics(MAP_AB)

        self.assertRasterFitsUnivar(raster=MAP_AB,
                precision=PRECISION, reference=ab_univar_string)

if __name__ == '__main__':
    from grass.gunittest.main import test
    test()
