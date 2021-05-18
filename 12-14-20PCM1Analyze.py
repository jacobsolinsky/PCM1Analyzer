from ij import IJ, WindowManager, ImagePlus
from ij.io import Opener
from ij.process import ImageConverter, ByteProcessor
import re
import os
from ij.plugin.frame import RoiManager
from ij.plugin import ImageCalculator
from ij.measure import ResultsTable
opener = Opener(); 
#This is the image directory. Make sure to put a subdirectory named "results" ointo this directory.
directory = r"F:\Sorensen\2-21PCM\Cropped"

try:
	os.mkdir(directory + r'\results')
except: pass



def get_pc_mask(pcpath):
  pc = opener.openImage(pcpath)
  ImageConverter(pc).convertToGray8()
  pc.getProcessor().threshold(0)
  pc.getProcessor().invert()
  pc.setTitle('pcMask')
  pc.show()
  pc2 = opener.openImage(pcpath)
  pc2.setTitle('pc')
  pc2.setDefault16bitRange(10)
  pc2.show()
  IJ.run("Set Measurements...", "modal redirect=pc decimal=3")
  IJ.run(pc, "Analyze Particles...", "display clear")
  rt = ResultsTable.getResultsTable()
  modal_grey_value = int(rt.getValue("Mode",0))
  IJ.log(str(int(rt.getValue("Mode",0))))
  IJ.run(pc, "Subtract...", "value=255")
  ImageConverter(pc).convertToGray16()
  IJ.run(pc, "Add...", "value={}".format(modal_grey_value))
  pc3 = ImageCalculator().run("max create", pc, pc2);
  pc.changes = False; pc.close()
  pc3.setTitle('pc')
  pc3.show()
  IJ.run(pc3, "Convert to Mask", "method=Otsu background=Dark")
  IJ.run(pc3, "Morphological Filters", "operation=Erosion element=Disk radius=1")
  pc3.changes = False
  pc3.close()
  pc3 = WindowManager.getImage('pc-Erosion')
  pc3.setTitle('pc')
  IJ.run(pc3, "Morphological Filters", "operation=Closing element=Disk radius=50")
  pc3.changes = False
  pc3.close()
  pc3= WindowManager.getImage('pc-Closing')
  return pc3




def collate(directory):
  regex = r"(?P<date>\d+-\d+-\d+)(?P<name>[^=-]+)=-Image Export-(?P<suffix>[^c]+)(?P<channel>c\d).*"
  retval = {}
  for filename in os.listdir(directory):
    res = re.match(regex, filename)
    if res:
      groupdict = res.groupdict()
      channel = groupdict.pop('channel')
      other = frozenset(groupdict.iteritems())
      if other not in retval:
        retval[other] = {}
      retval[other][channel] = r"{}\{}".format(directory, filename)
  return retval
    
  

rm = RoiManager.getRoiManager()
rm.runCommand("Associate", "true")
rm.runCommand("Show All without labels")
i = 1
for metadata, channeldict in collate(directory).iteritems():
      IJ.log(str(metadata))
      IJ.run("Set Measurements...", "area")
      #This opens the pcm1 image. The text here has to match the text that indicated the pcm1 image in the filename
      pcm1 = opener.openImage(channeldict['c3'])
      pcm1.show()
      pcm1.setTitle('pcm1')
      ImageConverter(pcm1).convertToGray8()
      #This function thresholds the
      threshold_radius = 15; threshold_method = "Otsu"
      IJ.run(pcm1, "Auto Local Threshold", "method={} radius={} parameter_1=0 parameter_2=0 white".format(threshold_method, threshold_radius))
      #this excludes all objects in the image that can't contain a 2-pixel-radius circle within them. This can be changed.
      IJ.run(pcm1, "Morphological Filters", "operation=Opening element=Disk radius=3")
      pcm1_opening = WindowManager.getImage("pcm1-Opening")
      pcm1_opening.show()
      pcm1.changes = False; pcm1.close()
      IJ.run(pcm1_opening, "Invert", "")
      #the size=11.00-240.00 can be altered to change how large the nuclei should be
      IJ.run(pcm1_opening, "Analyze Particles...", "size=11.00-240.00 pixel show=Masks")
      pcm1_opening.changes = False; pcm1_opening.close()
      pcm1_objects = WindowManager.getImage("Mask of pcm1-Opening")
      pcm1_objects.show()
      pcm1_objects.setTitle('pcm1_objects')



      #this opens the dapi image
      dapi = opener.openImage(channeldict['c1'])
      dapi.show()
      dapi.setTitle('dapi')



      
      #this opens a second copy of the pcm1 image for analysis
      pcm1_copy = opener.openImage(channeldict['c3'])
      pcm1_copy.show()
      pcm1_copy.setTitle('pcm1_copy')

      #This sets the measurements of the pcm1_objects onto the dapi image. Notice the redirect=dapi part, the name on the righthand side has to be the name of the image being measured
      IJ.run("Set Measurements...", "area mean centroid feret's integrated median redirect=dapi decimal=3")
      IJ.run(pcm1_objects, "Analyze Particles...", "display clear")
      rt = ResultsTable.getResultsTable()
      #This saves those measurements
      rt.saveAs(directory +r"\results\dapi_" + '_'.join("{}={}".format(k, v) for k, v in dict(metadata).iteritems()) + ".csv")

      #This sets the measurements of the pcm1_objects onto the pcm1 image
      IJ.run("Set Measurements...", "mean integrated median redirect=pcm1_copy decimal=3")
      IJ.run(pcm1_objects, "Analyze Particles...", "display clear")
      rt = ResultsTable.getResultsTable()
      rt.saveAs(directory +r"\results\pcm1_" + '_'.join("{}={}".format(k, v) for k, v in dict(metadata).iteritems()) + ".csv")

      
      
      try:
	      #this opens the edu image
	      edu = opener.openImage(channeldict['c4'])
	      edu.show()
	      edu.setTitle('edu')  
	      #This sets the measurements of the pcm1_objects onto the edu image
	      IJ.run("Set Measurements...", "mean integrated median redirect=edu decimal=3")
	      IJ.run(pcm1_objects, "Analyze Particles...", "display clear")
	      rt = ResultsTable.getResultsTable()
	      rt.saveAs(directory +r"\results\edu_" + '_'.join("{}={}".format(k, v) for k, v in dict(metadata).iteritems()) + ".csv")
      except KeyError:
	      pass

      
      try:
          #This sets the measurements of the pcm1_objects onto the ph3 image
          #this opens the ph3 image
          ph3 = opener.openImage(channeldict['c2'])
          ph3.show()
          ph3.setTitle('ph3')
	
          IJ.run("Set Measurements...", "mean integrated median redirect=ph3 decimal=3")
          IJ.run(pcm1_objects, "Analyze Particles...", "display clear")
          rt = ResultsTable.getResultsTable()
          rt.saveAs(directory +r"\results\ph3_" + '_'.join("{}={}".format(k, v) for k, v in dict(metadata).iteritems()) + ".csv")
      except KeyError:
	      pass
      
      IJ.run("Close All") 

  