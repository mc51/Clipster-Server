from setuptools import setup

setup(
    name="clipster-server",
    version="0.1",
    description="Multi Platform Cloud Clipboard - Linux Server",
    url="http://github.com/mc51/Clipster-Server",
    author="MC51",
    author_email="mc@data-dive.com",
    license="GNU GPL v3",
    packages=["clipster"],
    install_requires=["Django", "dj_database_url", "djangorestframework", "gunicorn"],
    python_requires=">=3.4",
    zip_safe=False,
    entry_points={"console_scripts": ["clipster = clipster.clipster:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
