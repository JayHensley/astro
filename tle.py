"""Download and handle TLEs
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np
import ephem
import pdb
from collections import defaultdict, namedtuple

from astro import time

deg2rad = np.pi/180
rad2deg = 180/np.pi
sec2day = 1 / ( 24 * 3600)
day2sec = 24 * 3600

# tuple to hold all the items from a single TLE 
TLE = namedtuple('TLE', [
    'satname', 'satnum', 'classification', 'id_year', 'id_launch',
    'id_piece', 'epoch_year', 'epoch_day', 'ndot_over_2', 'nddot_over_6',
    'bstar', 'ephtype', 'elnum', 'checksum1',
    'inc', 'raan', 'ecc', 'argp', 'ma', 'mean_motion', 'epoch_rev',
    'checksum2'])

def get_tle_ephem(filename):
    """Load TLEs from a file
    """
    satlist = []
    with open(filename,'r') as f:
        l1 = f.readline()
        while l1:
            l2 = f.readline()
            l3 = f.readline()
            sat = ephem.readtle(l1, l2, l3)
            satlist.append(sat)
            print(sat.name)
            l1 = f.readline()

    print("{} satellites loaded into list".format(len(satlist)))
    return satlist

# write my own TLE parser since ephem doesn't save all the values

def validtle(l0, l1, l2):
    """Quick check to make sure we have the three lines of a 3TLE
    """
    l0_valid_start = int(l0[0]) == 0
    l1_valid_start = int(l1[0]) == 1
    l2_valid_start = int(l2[0]) == 2

    l1_valid_length = len(l1) == 69
    l2_valid_length = len(l2) == 69

    l1_valid_checksum = int(l1[-1]) == checksum(l1)
    l2_valid_checksum = int(l2[-1]) == checksum(l2)
    return (l0_valid_start and l1_valid_start and l2_valid_start 
            and l1_valid_length and l2_valid_length and 
            l1_valid_checksum and l1_valid_checksum)

def checksum(line):
    """The checksums for each line are calculated by adding the all numerical
    digits on that line, including the line number. One is added to the
    checksum for each negative sign (-) on that line. All other non-digit
    characters are ignored.  @note this excludes last char for the checksum
    thats already there.
    """
    return sum(map(int, filter(
        lambda c: c >= '0' and c <= '9', line[:-1].replace('-','1')))) % 10


def stringScientificNotationToFloat(sn):
    """Specific format is 5 digits, a + or -, and 1 digit, ex: 01234-5 which is
    0.01234e-5
    """
    return 1e-5*float(sn[:6]) * 10**int(sn[6:]) 

def parsetle(l0, l1, l2):
    """
    The function parsetle extracts the elements of a two line element set.
    This takes in the three lines of a TLE and parses the values.

    Inputs:
    l0 - first line consiting of the name of TLE (optional)
    l1 - second line  
    l2 - third line

    Outputs - namedtuple TLE:
    satname - satellite name  
    satnum - satellite number found (0 if the requested sat was not found)
    classfication  - classification (classified, unclassified)
    id_year - launch year (last 2 digits)
    id_launch - launch number of the year
    id_piece - piece of launch (a string 3 characters long)
    epoch_year - epoch year (last 2 digits)
    epoch_day - epoch day of year
    ndot_over_2 - first time derive of mean mot. divided by 2 (rev/day^2)
    nddot_over_6 - 2nd deriv of mean mot div by 6 (rev/day^3)
    bstar - bstar drag term
    ephtype- ephemeris type
    elnum  - element number (modulo 1000)
    checksum1 - checksum of first line 

    inc    - inclination (deg)
    raan   - right ascension of asc. node (deg)
    ecc    - eccentricity
    argp    - argument of perigee (deg)
    ma     - mean anomaly (deg)
    mean_motion - mean motion (revs per day)
    epoch_rev - revolution number(modulo 100,000)
    checksum2 - checksum of second line

    References:
    "Fundamental of Astrodynamics and Applictions, 2nd Ed", by Vallado
    www.celestrak.com/NORAD/documentation/tle-fmt.asp
    manpages.debian.net/cgi-bin/...
    display_man.cgi?id=e2095ebad4eb81b943fcdd55ec9b7521&format=html
    """
    # parse line zero
    satname = l0[0:23]

    # parse line one
    satnum = int(l1[2:7])
    classification = l1[7:8]
    id_year = int(l1[9:11])
    id_launch = int(l1[11:14])
    id_piece = l1[14:17]
    epoch_year = int(l1[18:20])
    epoch_day = float(l1[20:32])
    ndot_over_2 = float(l1[33:43])
    nddot_over_6 = stringScientificNotationToFloat(l1[44:52])
    bstar = stringScientificNotationToFloat(l1[53:61])
    ephtype = int(l1[62:63])
    elnum = int(l1[64:68])
    checksum1 = int(l1[68:69])

    # parse line 2
    # satellite        = int(line2[2:7])
    inc = float(l2[8:16])
    raan = float(l2[17:25])
    ecc = float(l2[26:33]) * 0.0000001
    argp = float(l2[34:42])
    ma = float(l2[43:51])
    mean_motion = float(l2[52:63])
    epoch_rev = float(l2[63:68])
    checksum2 = float(l2[68:69])
    
    return TLE(satnum=satnum, classification=classification, id_year=id_year,
            id_launch=id_launch, id_piece=id_piece, epoch_year=epoch_year,
            epoch_day=epoch_day, ndot_over_2=ndot_over_2,
            nddot_over_6=nddot_over_6, bstar=bstar, ephtype=ephtype,
            elnum=elnum, checksum1=checksum1, inc=inc, raan=raan, ecc=ecc,
            argp=argp, ma=ma, mean_motion=mean_motion, epoch_rev=epoch_rev,
            checksum2=checksum2, satname=satname)

def j2dragpert(inc0, ecc0, n0, ndot2, mu=398600.5, re=6378.137, J2=0.00108263):

    """
    This file calculates the rates of change of the right ascension of the
    ascending node(raandot), argument of periapsis(argdot), and
    eccentricity(eccdot).  The perturbations are limited to J2 and drag only.

    Author:   C2C Shankar Kulumani   USAFA/CS-19   719-333-4741
            12 5 2014 - modified to remove global varaibles
            17 Jun 2017 - Now in Python for awesomeness

    Inputs:
    inc0 - initial inclination (radians)
    ecc0 - initial eccentricity (unitless)
    n0 - initial mean motion (rad/sec)
    ndot2 - mean motion rate divided by 2 (rad/sec^2)

    Outputs:
    raandot - nodal rate (rad/sec)
    argdot - argument of periapsis rate (rad/sec)
    eccdot - eccentricity rate (1/sec)

    Globals: None

    Constants:
    mu - 398600.5 Earth gravitational parameter in km^3/sec^2
    re - 6378.137 Earth radius in km
    J2 - 0.00108263 J2 perturbation factor

    Coupling: None

    References:
    Vallado
    """     
    
    # calculate initial semi major axis and semilatus rectum
    a0 = (mu / n0**2) ** (1/3)
    p0 = a0 * (1 - ecc0**2)

    # mean motion with J2
    nvec = n0 * (1 + 1.5 * J2 * (re/p0)**2 * np.sqrt(1-ecc0**2) * (1-1.5*np.sin(inc0)**2))

    # eccentricity rate
    eccdot = (-2 * (1-ecc0)*2*ndot2)/(3*nvec)

    # calculate nodal rate
    raandot = (-1.5*J2*(re/p0)**2*np.cos(inc0))*nvec

    # argument of periapsis rate
    argdot = (2.5*J2*(re/p0)**2*(2-2.5*np.sin(inc0)**2))*nvec

    return (raandot, argdot, eccdot)

def get_tle(filename):
    """Assuming a file with 3 Line TLEs is given this will parse the file
    and save all the elements to a list or something. 
    """
    sats = defaultdict(lambda: defaultdict(list))

    with open(filename, 'r') as f:
        l0 = f.readline().strip()
        while l0:
            l1 = f.readline().strip()
            l2 = f.readline().strip()
            # error check to make sure we have read a complete TLE
            if validtle(l0, l1, l2):
                # now we parse the tle
                elements = parsetle(l0, l1, l2)

                # now do some conversions of the TLE components
                epoch_year = (2000 + elements.epoch_year 
                        if elements.epoch_year < 70 
                        else 1900 + elements.epoch_year) 
                # working units 
                ndot2 = elements.ndot_over_2 * (2*np.pi) * (sec2day**2)
                inc0 = elements.inc * deg2rad
                raan0 = elements.raan * deg2rad
                argp0 = elements.argp * deg2rad
                ma0 = elements.ma * deg2rad
                mean_motion0 = elements.mean_motion * 2 * np.pi * sec2day**2
                ecc0 = elements.ecc
                n0 = elements.mean_motion
                epoch_day = elements.epoch_day

                # calculate perturbations raan, argp, ecc
                raandot, argpdot, eccdot = j2dragpert(inc0, ecc0, n0, ndot2)

                # calculate epoch julian date
                mo, day, hour, mn, sec = time.dayofyr2mdhms(epoch_year, epoch_day)
                epoch_jd = time.date2jd(epoch_year, mo, day, hour, mn, sec)

                # store into dictionary
            else:
                print("Invalid TLE")

            l0 = f.readline().strip()
