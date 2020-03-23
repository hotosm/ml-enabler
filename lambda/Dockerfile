FROM lambci/lambda:build-python3.7

WORKDIR /tmp

ENV PACKAGE_PREFIX /tmp/python

################################################################################
#                            CREATE PACKAGE                                    #
################################################################################
COPY download_and_predict download_and_predict
COPY setup.py setup.py

ENV \
  LANG=en_US.UTF-8 \
  LC_ALL=en_US.UTF-8 \
  CFLAGS="--std=c99"

RUN pip3 install . --no-binary numpy -t $PACKAGE_PREFIX -U

################################################################################
#                            REDUCE PACKAGE SIZE                               #
################################################################################
RUN rm -rdf $PACKAGE_PREFIX/boto3/ \
  && rm -rdf $PACKAGE_PREFIX/botocore/ \
  && rm -rdf $PACKAGE_PREFIX/docutils/ \
  && rm -rdf $PACKAGE_PREFIX/dateutil/ \
  && rm -rdf $PACKAGE_PREFIX/jmespath/ \
  && rm -rdf $PACKAGE_PREFIX/s3transfer/ \
  && rm -rdf $PACKAGE_PREFIX/numpy/doc/

# Leave module precompiles for faster Lambda startup
RUN find $PACKAGE_PREFIX -type f -name '*.pyc' | while read f; do n=$(echo $f | sed 's/__pycache__\///' | sed 's/.cpython-[2-3][0-9]//'); cp $f $n; done;
RUN find $PACKAGE_PREFIX -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf
RUN find $PACKAGE_PREFIX -type f -a -name '*.py' -print0 | xargs -0 rm -f

################################################################################
#                              CREATE ARCHIVE                                  #
################################################################################
RUN cd $PACKAGE_PREFIX && zip -r9q /tmp/package.zip *

# Cleanup
RUN rm -rf $PACKAGE_PREFIX
