from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="get-sms-online",
    version="1.0.0",
    description="Python SDK for the Get SMS Online API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/getsms-online/get.sms.online-python",
    author="Get SMS Online",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.20.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Communications :: Telephony",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="sms otp verification phone number api getsms tellabot",
)
