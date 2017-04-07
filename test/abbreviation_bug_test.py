#!/usr/bin/python
from .. import versioning

from pyspatialite import dbapi2
import psycopg2
import os
import tempfile

if __name__ == "__main__":
    tmp_dir = tempfile.gettempdir()
    test_data_dir = os.path.dirname(os.path.realpath(__file__))

    sqlite_test_filename = tmp_dir+"/versioning_base_test1.sqlite"
    if os.path.isfile(sqlite_test_filename):
        os.remove(sqlite_test_filename)

    # create the test database
    os.system("dropdb epanet_test_db")
    os.system("createdb epanet_test_db")
    os.system("psql epanet_test_db -c 'CREATE EXTENSION postgis'")
    os.system("psql epanet_test_db -f "+test_data_dir+"/epanet_test_db.sql")

    pcon = psycopg2.connect("dbname=epanet_test_db")
    pcur = pcon.cursor()
    for i in range(10):
        pcur.execute("""
            INSERT INTO epanet.junctions
                (id, elevation, geom)
                VALUES
                ('{id}', {elev}, ST_GeometryFromText('POINT({x} {y})',2154));
            """.format(
                id=str(i+2)+'_this_is_a_very_long_name_that should_be_trunctated_if_buggy',
                elev=float(i),
                x=float(i+1),
                y=float(i+1)
                ))
    pcon.commit()
    pcon.close()

    versioning.checkout("dbname=epanet_test_db",["epanet_trunk_rev_head.junctions","epanet_trunk_rev_head.pipes"], sqlite_test_filename)
    assert( os.path.isfile(sqlite_test_filename) and "sqlite file must exist at this point" )

    scon = dbapi2.connect(sqlite_test_filename)
    scur = scon.cursor()
    scur.execute("SELECT * from junctions")
    for rec in scur:
        if rec[0] > 2:
            assert rec[1].find('_this_is_a_very_long_name_that should_be_trunctated_if_buggy') != -1