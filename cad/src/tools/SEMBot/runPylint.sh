#!/bin/sh

# $Id$

# Usage: ./runPylint.sh &>Pylint.log

# Run Pylint 
pushd SVN-D/cad/src

# Remove old reports
rm -rf pylint_*

BATCH_NUMBER=0
# Some files break Pylint, exclude them
CAPITAL_M_STAR=`ls M*.py|grep -v MWsemantics.py`
CAPITAL_T_STAR=`ls T*.py|grep -v TreeView.py|grep -v TreeWidget.py`
PM_STAR=`ls PM/PM_*.py|grep -v PM_CheckBox|grep -v PM_Slider.py`
# Run in batches
for batch in `find . -type f -name "*.py" | grep -v .svn | grep -v experimental | grep -v tools | grep -v outtakes | grep -v scratch | grep -v .png` 
do
  echo "Running batch $BATCH_NUMBER: $batch"
  /usr/local/bin/pylint --rcfile=../../../Pylint.rcfile $batch

  # Post process results
  ../../../pylint_global.pl pylint_global.txt ${BATCH_NUMBER} pylint.${BATCH_NUMBER}.result > pylint_global.${BATCH_NUMBER}.html

  let BATCH_NUMBER=BATCH_NUMBER+1
done

# Aggregate code "grades"
echo "scale=3" > tmp.txt
echo "average=("`cat pylint.0.result`+`cat pylint.1.result`+`cat pylint.2.result`+`cat pylint.3.result`+`cat pylint.5.result`+`cat pylint.6.result`+`cat pylint.7.result`+`cat pylint.8.result`+`cat pylint.9.result`+`cat pylint.10.result`+`cat pylint.11.result`+`cat pylint.12.result`")/13" >> tmp.txt
echo "if (average > 2.5) {" >> tmp.txt
echo "  if (average > 5.0) {" >> tmp.txt
echo "    if (average > 7.5) {" >> tmp.txt
echo "      ;" >> tmp.txt
echo "    } else {" >> tmp.txt
echo "      \"<font style=\"; print \"\q\"; \"color: #ffffff; background: #3ab0b6\"; print \"\q\"; \">&nbsp;\"" >> tmp.txt
echo "    }" >> tmp.txt
echo "  } else {" >> tmp.txt
echo "    \"<font style=\"; print \"\q\"; \"color: #ffffff; background: #fd5053\"; print \"\q\"; \">&nbsp;\"" >> tmp.txt
echo "  }" >> tmp.txt
echo "} else {" >> tmp.txt
echo "  \"<font style=\"; print \"\q\"; \"color: #ffffff; background: #ff0000\"; print \"\q\"; \">&nbsp;\"" >> tmp.txt
echo "}" >> tmp.txt
echo "average; \"</font>\"" >> tmp.txt
echo "quit" >> tmp.txt
echo `bc -q tmp.txt` > ../../../Pylint.result
rm pylint.?.result tmp.txt

popd

# Generate filtered summary reports:
# (their output files have links in index.php)

# W0403 - Relative import %s. Emitted when an import statement uses a package-relative pathname.
grep W0403 SVN-D/cad/src/pylint_* > W0403.txt

# W0611 - Unused import %s. Emitted when an imported module or variable is not used.
grep W0611 SVN-D/cad/src/pylint_* > W0611.txt

# E0602 - Undefined variable %s. Emitted when a non-builtin symbol is used, but no 
# definition or import of it can be found.
grep E0602 SVN-D/cad/src/pylint_* > E0602.txt

# Consider adding summary reports for the following:
# W0311 - Bad indentation
# ? - Tabs in indentation

# end
