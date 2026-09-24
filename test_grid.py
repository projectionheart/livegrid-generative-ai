import unittest
import numpy as np
from grid import cells,calibration,compose,SIZE
from app import update,settings

class GridTests(unittest.TestCase):
    def test_exact_coverage(self):
        cover=np.zeros((SIZE,SIZE),dtype=np.uint8)
        for cell in cells():
            x,y,w,h=cell['pixels']; self.assertEqual(w,h)
            cover[y:y+h,x:x+w]+=1
        self.assertEqual(len(cells()),100)
        self.assertTrue(np.all(cover==1))
    def test_top_left_numbering(self):
        self.assertEqual(cells()[0]['pixels'],[0,0,108,108])
        self.assertEqual(cells()[-1]['pixels'],[972,972,108,108])
    def test_gap_and_repeat(self):
        src=np.full((512,512,3),255,np.uint8)
        out=compose(src,'repeat',4)
        self.assertTrue(np.all(out[:4]==0))
        self.assertTrue(np.all(out[4:108,4:108]==255))
        self.assertEqual(calibration().shape,(1080,1080,3))
    def test_control_validation_is_atomic(self):
        previous=settings.copy()
        for invalid in ({'speed':float('nan')},{'gap':99},{'blackout':'false'},{'layout':'bad'},{'prompt':'x','brightness':2}):
            with self.assertRaises(ValueError): update(invalid)
            self.assertEqual(settings,previous)

if __name__=='__main__': unittest.main()
