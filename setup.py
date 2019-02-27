from setuptools import setup


def read_readme():
    with open("README.rst") as file:
        return file.read()


setup(name='pycp',
      version="8.0.8",
      description='cp and mv with a progressbar',
      long_description=read_readme(),
      author="Dimitri Merejkowsky",
      author_email="d.merej@gmail.com",
      url='http://github.com/dmerejkowsky/pycp',
      packages=['pycp'],
      license='COPYING',
      install_requires=[
          "attrs",
      ],
      extras_require={
          "dev": [
              "path.py",
              "pycodestyle",
              "pyflakes",
              "pylint",
              "mccabe",
              "pytest",
              "pytest-mock",
              "bumpversion",
              "twine",
              "wheel",
          ]
      },
      entry_points={
          "console_scripts": [
              "pycp = pycp.main:main",
              "pymv = pycp.main:main",
            ]
      },
      classifiers=[
        "Environment :: Console",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Shells",
      ],
      )
