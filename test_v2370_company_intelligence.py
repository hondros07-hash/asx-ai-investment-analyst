import unittest
from services.company_intelligence_engine import orchestrate_company_synthesis as run
class CompanyIntelligenceTests(unittest.TestCase):
 def setUp(self):
  self.ex=[{'exposure_key':'consumer_credit_loss_sensitive','verified':True,'source':'Official filing','evidence_id':'a1'}]
  self.event={'source_type':'announcement','event_key':'credit_loss_rate','direction':'up','what_changed':'Verified credit loss rate increased','ticker':'ZIP.AX','verified':True,'source':'Official filing','evidence_id':'e1'}
 def test_missing_event(self):self.assertEqual(run('ZIP.AX')['status'],'insufficient_evidence')
 def test_headline_not_verified(self):self.assertEqual(run('ZIP.AX',raw_event={**self.event,'verified':False},exposures=self.ex)['status'],'insufficient_evidence')
 def test_mismatched_ticker(self):self.assertEqual(run('QAN.AX',raw_event=self.event,exposures=self.ex)['status'],'insufficient_evidence')
 def test_verified_mapping(self):
  r=run('ZIP.AX',raw_event=self.event,exposures=self.ex,thesis_conditions=[{'metric':'credit_losses_remain_controlled','status':'watch'}]);self.assertEqual((r['status'],r['thesis_impact'],r['directional_pressure']),('mapped','watch','negative'))
 def test_unmapped(self):self.assertEqual(run('ZIP.AX',raw_event={**self.event,'event_key':'unknown'},exposures=self.ex)['status'],'insufficient_evidence')
if __name__=='__main__':unittest.main()
