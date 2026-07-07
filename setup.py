import sys
sys.path.insert(0, 'AWSIoTPythonSDK')
import AWSIoTPythonSDK
currentVersion = AWSIoTPythonSDK.__version__

from setuptools import setup
setup(
    name = 'AWSIoTPythonSDK',
    packages=['AWSIoTPythonSDK', 'AWSIoTPythonSDK.core',
              'AWSIoTPythonSDK.core.util', 'AWSIoTPythonSDK.core.shadow', 'AWSIoTPythonSDK.core.protocol',
              'AWSIoTPythonSDK.core.jobs',
              'AWSIoTPythonSDK.core.protocol.paho', 'AWSIoTPythonSDK.core.protocol.internal',
              'AWSIoTPythonSDK.core.protocol.connection', 'AWSIoTPythonSDK.core.greengrass',
              'AWSIoTPythonSDK.core.greengrass.discovery', 'AWSIoTPythonSDK.exception'],
    version = currentVersion,
    description = 'SDK for connecting to AWS IoT using Python.',
    author = 'Amazon Web Service',
    author_email = '',
    url = 'https://github.com/aws/aws-iot-device-sdk-python.git',
    download_url = 'https://s3.amazonaws.com/aws-iot-device-sdk-python/aws-iot-device-sdk-python-latest.zip',
    keywords = ['aws', 'iot', 'mqtt'],
    classifiers = [
        "Development Status :: 6 - Mature",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3"
    ]
)
