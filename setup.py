from setuptools import setup

setup(
    name="clipster-server",
    version="0.4.2",
    description="Multi Platform Cloud Clipboard - Linux Server",
    url="http://github.com/mc51/Clipster-Server",
    author="MC51",
    author_email="mc@data-dive.com",
    license="MIT",
    packages=["clipster"],
    install_requires=[
        "Django",
        "dj_database_url",
        "djangorestframework",
        "gunicorn",
        "whitenoise",
    ],
    python_requires=">=3.6",
    zip_safe=False,
    entry_points={"console_scripts": ["clipster = clipster.clipster:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
