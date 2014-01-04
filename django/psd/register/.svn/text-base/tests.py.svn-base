"""
run "manage.py test".
"""

from django.test import TestCase
from models import Person, RegRecord, Event
from matchmaker import make_sym_matrix
import debugtools
from psd.psdmanage import *

class RegTestCase(TestCase):
    def all_equal(self, *pairs):
        for p in pairs:
            self.assertEqual(*p)


    def setUp(self):
        makeTestDB( False )
        self.event = Event.objects.get( event="testing1" )
                
        self.bob = Person(
            first_name = 'Bob',
            gender = 'M',
            age = 42,
            seeking_primary = True,
            kinky = False,
            seek_gender = 'W',
            seek_age_min = 18,
            seek_age_max = 42,
            seek_kinkiness = 'EI')
        self.bob.save()

        self.bob_reg = RegRecord(
            psdid = "bob",
            is_group = False,
            location = 'SF',
            event="testing1"
        )
        self.bob_reg.save()

        self.bob_reg.people.add(self.bob)
        self.bob_reg.save()
        
        self.gayboy = Person(
            first_name = 'gayboy',
            gender = 'M',
            age = 52,
            seeking_primary = True,
            kinky = True,
            seek_gender = 'M-2,Q',
            seek_age_min = 18,
            seek_age_max = 42,
            seek_kinkiness = 'EI')
        self.gayboy.save()

        self.gayboy_reg = RegRecord(
            psdid = "gayboy",
            is_group = False,
            location = 'SF',
            event="testing1"
            
        )
        self.gayboy_reg.save()

        self.gayboy_reg.people.add(self.gayboy)
        self.gayboy_reg.save()
        
        self.lulu = Person(
            first_name = "Lulu",
            gender = 'W',
            age = 42,
            seeking_primary = False,
            kinky = True,
            seek_gender = 'M,W,TM,TW,Q',
            seek_age_min = 24,
            seek_age_max = 55,
            seek_kinkiness = 'EI')
        self.lulu.save()

        self.lulu_reg = RegRecord(
            psdid = "lulu",
            is_group = False,
            location = 'SF,EB',
            event="testing1"
            
        )
        self.lulu_reg.save()

        self.lulu_reg.people.add(self.lulu)
        self.lulu_reg.save()
              
        self.omni = Person(
            first_name="omni",
            gender = 'W,TW',
            age = 42,
            seeking_primary = False,
            kinky = True,
            seek_gender = 'M-2,W,TM-2,TW,Q,GQ,NA,BU,FE,AN',
            seek_age_min = 24,
            seek_age_max = 60,
            seek_kinkiness = 'K')
        self.omni.save()

        self.omni_reg = RegRecord(
            psdid = "omni",
            is_group = False,
            location = 'SE',
            event="testing1"
            
        )
        self.omni_reg.save()

        self.omni_reg.people.add(self.omni)       
        self.omni_reg.save()        
        
        self.omni2 = Person(
            first_name="omni2",
            gender = 'W,TW',
            age = 42,
            seeking_primary = False,
            kinky = True,
            seek_gender = 'M-2,W,TM-2,TW,Q,GQ,NA,BU,FE,AN',
            seek_age_min = 24,
            seek_age_max = 60,
            seek_kinkiness = 'K')
        self.omni2.save()

        self.omni2_reg = RegRecord(
            psdid = "omni2",
            is_group = False,
            location = 'SB,EB',
            event="testing1"
            
        )
        self.omni2_reg.save()

        self.omni2_reg.people.add(self.omni2)   
        self.omni2_reg.save()
                

    def tearDown(self):
        self.bob_reg.delete()
        self.lulu_reg.delete()
        self.omni_reg.delete()
        self.omni2_reg.delete()
        self.bob.delete()
        self.lulu.delete()
        self.omni.delete()
        self.omni2.delete()
        
    def test_Bob(self):
        bob = self.bob
        self.all_equal(
            (bob.first_name, 'Bob'),
            (bob.gender_set, set('M')),
            (bob.seek_gender_set, set('W')),
            (bob.will_date_kinky, True),
            (bob.will_date_nonkinky, True),
        )

    def test_Omni(self):
        omni = self.omni
        self.all_equal(
            (omni.first_name, 'omni'),
            (omni.gender_set, set(['W','TW'])),
            (omni.pref_gender_set, set(['M','TM'])),
            (omni.will_date_kinky, True),
            (omni.will_date_nonkinky, False),
        )

    def test_Bob_reg(self):
        r = self.bob_reg
        self.all_equal(
            (r.integrity_ok(), True),
            (r.indiv, self.bob),
            (r.is_group, False),
            (r.genders, set('M')),
            (r.has_gender('M'), True),
            (r.has_gender('W'), False),
            (r.wants_gender('M'), False),
            (r.wants_gender('W'), True),
            (r.wants_mf, False),
            (r.is_man_only, True),
            (r.treat_as_woman, False),
            (r.location_set,set(['SF'])),
        )

    def test_Omni_reg(self):
        r = self.omni_reg
        self.all_equal(
            (r.integrity_ok(), True),
            (r.indiv, self.omni),
            (r.is_group, False),
            (r.location_set,set(['SE'])),
        )
        
    def test_Omni2_reg(self):
        r = self.omni2_reg
        self.all_equal(
            (r.integrity_ok(), True),
            (r.indiv, self.omni2),
            (r.is_group, False),
            (r.location_set,set(['SB','EB'])),
        )
        
    def test_Omni_Gender(self):
        r = self.omni_reg
        self.assertEqual( r.genders, set(['W','TW']) )
        self.assertEqual( r.has_gender('W'), True )
        self.assertEqual( r.has_gender('TW'), True )
        
        
    def test_Omni_Want_Gender(self):
        r = self.omni_reg
        self.all_equal(
            (r.wants_gender('BU'), True),
            (r.wants_gender('Q'), True),
            (r.wants_mf, True),
            (r.wants_m, True),
            (r.wants_f, True),
            (r.is_man_only, False) )
    
    def test_Omni_Treat_Gender(self):
        r = self.omni_reg
        self.assertEqual( r.treat_as_woman, True )
        self.assertEqual( r.treat_as_man, False )
        
    def test_Lulu_reg(self):
        r = self.lulu_reg
        self.all_equal(
            (r.integrity_ok(), True),
            (r.indiv, self.lulu),
            (r.is_group, False),
            (r.genders, set('W')),
            (r.has_gender('M'), False),
            (r.has_gender('W'), True),
            (r.wants_gender('M'), True),
            (r.wants_gender('W'), True),
            (r.wants_mf, True),
            (r.treat_as_woman, True),
            (r.location_set,set(['SF','EB'])),
        )


    def test_person_interest_basic(self):
        """
        Typical straight man looking for woman (who is looking for many things and thus
        likes the straight man
        """
        bob = self.bob
        lulu = self.lulu
        self.assertTrue(bob.will_date_basic(lulu))
        self.assertFalse(bob.will_date_basic(bob))
        self.assertTrue(lulu.will_date_basic(lulu))
        self.assertTrue(lulu.will_date_basic(bob))


    def test_person_interest(self):
        """
        Typical straight man looking for woman (who is looking for many things and thus
        likes the straight man
        """
        bob = self.bob
        lulu = self.lulu
        event = self.event
        self.assertTrue(bob.will_date(lulu, event))
        self.assertFalse(bob.will_date(bob, event))
        self.assertTrue(lulu.will_date(lulu, event))
        self.assertTrue(lulu.will_date(bob, event))
        self.assertEqual(bob.interest_score(lulu, event), 1)
        self.assertEqual(lulu.interest_score(bob, event), 3)
        self.assertEqual(lulu.interest_score(lulu, event), 5)


    def test_record_interest(self):
        bob = self.bob_reg
        lulu = self.lulu_reg
        event = self.event
        self.assertEqual(lulu.ok_gay_match(bob),False)
        self.assertEqual(lulu.ok_match(bob, 'gay'),False)
        self.assertFalse(bob.mf_gender_match(lulu))
        self.assertTrue(bob.mf_gender_cross(lulu))
        self.assertFalse(lulu.mf_gender_match(bob))
        self.assertTrue(lulu.mf_gender_cross(bob))
        self.assertTrue(bob.location_overlap(bob))
        self.assertTrue(bob.location_overlap(lulu))
        self.assertEqual(bob.interest_score(bob),0)
        self.assertEqual(bob.interest_score(lulu),3)
        self.assertEqual(lulu.interest_score(bob),5)
        self.assertEqual(lulu.interest_score(lulu),7)
        self.assertTrue(bob.ok_match(lulu, 'all'))
        self.assertTrue(bob.ok_match(lulu, 'str'))
        self.assertTrue(bob.ok_match(lulu, 'gay'))
        self.assertTrue(lulu.ok_match(bob, 'all'))
        self.assertTrue(lulu.ok_match(bob, 'str'))
        self.assertFalse(lulu.ok_match(bob, 'gay'))
        self.assertEqual(bob.matrix_score(lulu, 'all'), 3)
        self.assertEqual(lulu.matrix_score(bob, 'all'), 5)
        self.assertEqual(lulu.matrix_score(bob, 'gay'), 0)

    def test_record_interest_2(self):
        bob = self.bob_reg
        lulu = self.lulu_reg
        omni = self.omni_reg
        self.assertEqual( omni.interest_score(lulu),5 )
        self.assertEqual( omni.interest_score(bob), 0 )
        self.assertEqual( omni.interest_score(omni),7 )
        self.assertEqual( bob.interest_score(omni), 0 )
        self.assertEqual( lulu.interest_score(omni) , 5 )
        
        
    def test_matrices(self):
        gm,sm,am = [make_sym_matrix(t) for t in ('gay','str','all')]
        bob = self.bob_reg
        lulu = self.lulu_reg
        for m in (gm,sm,am):
            self.assertEqual(m[bob,lulu],m[lulu,bob])
        self.assertEqual(am[bob,lulu],3)
        self.assertEqual(sm[bob,lulu],3)
        self.assertEqual(gm[bob,lulu],0)

    def test_full_matrix(self):
        lst = [self.bob_reg,self.gayboy_reg,self.lulu_reg,self.omni_reg,self.omni2_reg]
        
        print "\n\n\n"
        for l in lst:
            print "%s\t%s" % (l.psdid, l.minicode() )
        
        mat = [[0 for i in range(len(lst))] for j in range(len(lst))]
        op = ""
        for (il,l) in enumerate(lst):
            for (rl,r) in enumerate(lst):
                insc = l.interest_score(r)
                mat[il][rl] = insc
                op += "%s -> %s = %s\n" % (l.psdid,r.psdid, insc )
        
        print op, "\n\n\n"
        
        baseline_output="""bob -> bob = 0
bob -> gayboy = 0
bob -> lulu = 3
bob -> omni = 0
bob -> omni2 = 0
gayboy -> bob = 7
gayboy -> gayboy = 0
gayboy -> lulu = 0
gayboy -> omni = 0
gayboy -> omni2 = 0
lulu -> bob = 5
lulu -> gayboy = 5
lulu -> lulu = 7
lulu -> omni = 5
lulu -> omni2 = 7
omni -> bob = 0
omni -> gayboy = 7
omni -> lulu = 5
omni -> omni = 7
omni -> omni2 = 5
omni2 -> bob = 0
omni2 -> gayboy = 7
omni2 -> lulu = 7
omni2 -> omni = 5
omni2 -> omni2 = 7
"""
        self.assertEqual( op, baseline_output )

    def makeTableTable(self):
        psd.register.views.dashboard.make_table_table( "testing1", 20, [1,2,3,4], [3,4,5,6,7] )
        

    def makeAndSaveDaterMatrix(self):
        updateMatchRecords( "testing1" )
        

    def testMarkAllHereAndSchedule(self):
        rrs = RegRecord.objects.all()
        for r in rrs:
            r.here = True
            r.save()
        
        schedule("testing1", 3, 2, who_include="In")
        
    def pdfGeneration(self):
        sch = register.views.printouts.make_schedule_pdf("testing1", "In")
        self.assertTrue( not (sch is None) )
        