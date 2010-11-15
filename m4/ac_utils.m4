
#
# CHECK_VERSION(FOUND-VERSION, MINIMUM-VERSION)
#
# Handles versions of the forms x.y and x.y.z where z can be lowercase letters
# and numbers. If z has letters, everything from the first letter to the end of
# the string is thrown out.
#
# Sets CHECK_VERSION_RESULT to 0 if the found- and minimum-versions are the
# same; to 1 if the found-version is later than the minimum-version; to -1 if
# the found-version is earlier than the minimum-version.
#
AC_DEFUN([CHECK_VERSION], [
	found_version=$1
	min_version=$2

	# Determine if we're of the form x.y or x.y.z
	found_form=`echo $found_version | sed 's/[[0-9]]*\.[[0-9]]*\.[[0-9a-z]]*/DOT_DOT/'`
	min_form=`echo $min_version | sed 's/[[0-9]]*\.[[0-9]]*\.[[0-9a-z]]*/DOT_DOT/'`

	if test "$found_form" = "DOT_DOT"; then
		found_major_version=`echo $found_version | \
			sed 's/^\([[0-9]]*\)\.\([[0-9]]*\)\.\([[0-9a-z]]*\)$/\1/'`
		found_minor_version=`echo $found_version | \
			sed 's/^\([[0-9]]*\)\.\([[0-9]]*\)\.\([[0-9a-z]]*\)$/\2/'`
		found_micro_version=`echo $found_version | \
			sed 's/^\([[0-9]]*\)\.\([[0-9]]*\)\.\([[0-9]]*\)[[0-9a-z]]*$/\3/'`
	else
		found_major_version=`echo $found_version | \
			sed 's/^\([[0-9]]*\)\.\([[0-9]]*\)$/\1/'`
		found_minor_version=`echo $found_version | \
			sed 's/^\([[0-9]]*\)\.\([[0-9]]*\)$/\2/'`
		found_micro_version=0
	fi

	# Parse version strings
	if test "$min_form" = "DOT_DOT"; then
		min_major_version=`echo $min_version | \
			sed 's/^\([[0-9]]*\)\.\([[0-9]]*\)\.\([[0-9a-z]]*\)$/\1/'`
		min_minor_version=`echo $min_version | \
			sed 's/^\([[0-9]]*\)\.\([[0-9]]*\)\.\([[0-9a-z]]*\)$/\2/'`
		min_micro_version=`echo $min_version | \
			sed 's/^\([[0-9]]*\)\.\([[0-9]]*\)\.\([[0-9]]*\)[[0-9a-z]]*$/\3/'`
	else
		min_major_version=`echo $min_version | \
			sed 's/^\([[0-9]]*\)\.\([[0-9]]*\)$/\1/'`
		min_minor_version=`echo $min_version | \
			sed 's/^\([[0-9]]*\)\.\([[0-9]]*\)$/\2/'`
		min_micro_version=0
	fi

	#echo Found $found_form :  $found_major_version X $found_minor_version X $found_micro_version
	#echo Min $min_form : $min_major_version X $min_minor_version X $min_micro_version

	# Compare versions
	if test $found_major_version -eq $min_major_version && \
	   test $found_minor_version -eq $min_minor_version && \
	   test $found_micro_version -eq $min_micro_version; then
		version_result=0
	else
		version_result=-1
		if test $found_major_version -gt $min_major_version; then
			version_result=1
		elif test $found_major_version -eq $min_major_version && \
			 test $found_minor_version -gt $min_minor_version; then
			version_result=1
		elif test $found_major_version -eq $min_major_version && \
			 test $found_minor_version -eq $min_minor_version && \
			 test $found_micro_version -ge $min_micro_version; then
			version_result=1
		fi
	fi

	AC_SUBST(CHECK_VERSION_RESULT, $version_result)
])


#
# CHECK_DESIRED_VERSION(LIBRARY-NAME, DESIRED-VERSION, FOUND-VERSION)
#
AC_DEFUN([CHECK_DESIRED_VERSION], [
	library_name=$1
	desired_version=$2
	found_version=$3

	if test "$STRICT_LIBRARY_CHECK" = "yes"; then
		AC_MSG_CHECKING(for $library_name version == $desired_version)
	else
		AC_MSG_CHECKING(for $library_name version >= $desired_version)
	fi

	CHECK_VERSION($found_version, $desired_version)
	version_check=$CHECK_VERSION_RESULT
	if test $version_check -lt 0; then
		AC_MSG_RESULT(no)
		echo "*** $library_name version $desired_version or later is required, but version $found_version "
            echo "*** was found instead. Please update your $library_name to version $desired_version."
		exit -1
	elif test $version_check -gt 0; then
		if test "$STRICT_LIBRARY_CHECK" = "yes"; then
			AC_MSG_RESULT(no)
		else
			AC_MSG_RESULT(yes)
		fi
		echo "### $library_name version $found_version was found. That version may work, but the"
		echo "### officially supported version is $desired_version."
		if test "$STRICT_LIBRARY_CHECK" = "yes"; then
			echo "*** Strict library check failed. Either install the officially supported"
			echo "*** version, or don't use the --enable-strict-library-check option."
			exit -1
		fi
	else
		AC_MSG_RESULT(yes)
	fi
])

#
# TEST_CHECK_DESIRED_VERSION_ONE(DESIRED-VERSION, FOUND-VERSION, SHOULD-OK)
#
AC_DEFUN([TEST_CHECK_DESIRED_VERSION_ONE], [
	desired_version=$1
	found_version=$2
	should_ok=$3

	AC_MSG_CHECKING(check_version $desired_version vs $found_version must $should_ok)
	CHECK_VERSION($found_version, $desired_version)
	if test "$should_ok" == "yes"; then
		test $CHECK_VERSION_RESULT -ge 0 || AC_MSG_ERROR(fault)
	else
		test $CHECK_VERSION_RESULT -lt 0 || AC_MSG_ERROR(fault)
	fi
	AC_MSG_RESULT(yes)
])

#
# TEST_CHECK_DESIRED_VERSION()
#
AC_DEFUN([TEST_CHECK_DESIRED_VERSION], [
	TEST_CHECK_DESIRED_VERSION_ONE("4.0", "4.5", yes)
	TEST_CHECK_DESIRED_VERSION_ONE("4.0", "4.5", yes)
	TEST_CHECK_DESIRED_VERSION_ONE("4.0", "5.6", yes)
	TEST_CHECK_DESIRED_VERSION_ONE("4.0.1", "5.6", yes)
	TEST_CHECK_DESIRED_VERSION_ONE("4.0", "5.6.1", yes)
	TEST_CHECK_DESIRED_VERSION_ONE("4.0.2", "5.6.1", yes)

	TEST_CHECK_DESIRED_VERSION_ONE("6.0.2", "5.6.1", no)
	TEST_CHECK_DESIRED_VERSION_ONE( "6.0", "5.6.1", no)
	TEST_CHECK_DESIRED_VERSION_ONE("6.0.2", "5.6", no)
])

