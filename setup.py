import sys
sys.path.insert(0, 'AWSIoTPythonSDK')
import AWSIoTPythonSDK
currentVersion = AWSIoTPythonSDK.__version__

from distutils.core import setup
setup(
    name = 'AWSIoTPythonSDK',
    packages = ['AWSIoTPythonSDK', "AWSIoTPythonSDK.core", \
                "AWSIoTPythonSDK.exception", "AWSIoTPythonSDK.core.shadow", \
                "AWSIoTPythonSDK.core.util", \
                "AWSIoTPythonSDK.core.protocol", "AWSIoTPythonSDK.core.protocol.paho", \
                "AWSIoTPythonSDK.core.protocol.paho.securedWebsocket"],
    version = currentVersion,
    description = 'SDK for connecting to AWS IoT using Python.',
    author = 'Amazon Web Service',
    author_email = '',
    url = 'https://github.com/aws/aws-iot-device-sdk-python.git',
    download_url = 'https://s3.amazonaws.com/aws-iot-device-sdk-python/aws-iot-device-sdk-python-latest.zip',
    keywords = ['aws', 'iot', 'mqtt'],
    classifiers = [
        "Development Status :: 5 - Production/Stable", \
        "Intended Audience :: Developers", \
        "Natural Language :: English", \
        "License :: OSI Approved :: Apache Software License", \
        "Programming Language :: Python", \
        "Programming Language :: Python :: 2.7", \
        "Programming Language :: Python :: 3", \
        "Programming Language :: Python :: 3.3", \
        "Programming Language :: Python :: 3.4", \
        "Programming Language :: Python :: 3.5"
    ]
)
