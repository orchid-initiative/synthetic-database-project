# Developer Guide
## Table of Contents
<!--ts-->
 * [Working with synthea](#Working-with-synthea)
  * [Outputs](#Outputs)
   * [Log files](#Log-files)
<!--te-->

## Working with synthea
### Outputs
#### Log files
- You will find full_synthea_stdout_[date]_[time].txt in the project directory
  - This is a raw log version of the java run you can reference if the run hits programtic issues and to cross reference with your data input/output
- You will find run_synthea.py_[date].log in the project directory
  - This is our helper function logging.  It provides some wrapper logging for the java function, much of the same java logging as above, and some timing statistics
  - This also provides some debugging opportunity for the formatting operations of our summary output.
#### /output/ files
  - Running synthea will create the output folder in your project directory.  This folder is where all patient records will be exported. Files will be exported to subfolders based on their type
  - Specifically, you have the option to configure synthea (see "**Configurations**" below)
  - Some description of the possible CSV summary outputs are documented here [LINK](https://github.com/synthetichealth/synthea/wiki/CSV-File-Data-Dictionary)

### Configurations
- Synthea runs with a multitude of optional settings, specified in a standalone text file in your project directory.  We name this file "synthea_settings"
- Some description of this file and its use is documented here [LINK](https://github.com/synthetichealth/synthea/wiki/Common-Configuration)
- The original default settings document from synthea org can be referenced here [LINK](https://github.com/synthetichealth/synthea/blob/master/src/main/resources/synthea.properties)

## Appendix Tools
### Installing a Virtual Machine
Even if you use a PC in the general course of business, you may still find it more convenient to code in a unix OS.
A lightweight Linux VM from somewhere like VMware player can be a quick and easy solution.

#### Downloading and setting up the Linux VM (time required: ~30-60 min):
- Download latest VMware player (free) [LINK](https://www.vmware.com/go/downloadplayer)
- Download a Linux installation to use on the VM (free)
  - Try Mint XFCE first - its lightweight and might be all we need [LINK](https://www.linuxmint.com/edition.php?id=294)
  - Save the iso to a directory of your choice
- Create the VM with the Linux installation
  - Detailed Steps: [LINK](https://thesecmaster.com/step-by-step-procedure-to-install-linux-mint-linux-on-vmware-workstation/)
  - Highlights:
    - “Create a new Virtual Machine” and choose “I will install the operating system later”
    - Select a guest operating system: Linux with version “other linux 5.x kernel 64-bit”
    - Might want at least 100gb of space for your VM filesystem. **the synthea data logs can get big**
      - As an aside - if you ever try to log into your VM and it loops on the login page the likely culprit is low disk space - enter the terminal with "ctr-alt-f1" and login there, then proceed to delete some files to free up space.  Start with the raw /output/fhir/ files from synthea runs.
    - Right click on your new VM in the home menu of VMware workstation and go into settings
      - Allocate more memory - maybe 4gb depending on how much your physical machine has.  I have 32gb RAM and usually only use up to half of it so 4-8 would be fine to allocate when using I think
      - I increased processors to 4 - no idea how important this is
      - Under CD/DVD (IDE) select “use ISO image file” and point to where you put your Mint ISO
      - No further changes to settings
    - Hit “play virtual machine” - it will send you to a welcome screen and auto start linux mint after a 10 sec count down.
    - Once launched and at the desktop screen for linux click “install linux mint” and proceed to step “b” below
  - Go through the install, reboot, and then setup instructions
      - You can safely select “erase disk and install linux mint” this is only referring to the VM disk space you allocated in step 3.a.iii.
    - After the install finishes, restart.
    - Once it boots back up you move onto configuration suggestions - make sure not to enable timeshift - it eats up your disk space and makes it difficult to login ([reference topic discussion](https://forums.linuxmint.com/viewtopic.php?p=2059143))
    - I did the update manager with whatever it suggested.  Select the banner that suggest you “change mirror to a local one” to make this much much faster.  In the popup just click on the two sources and give it a sec to test speeds and select the top speed option for each.
    - Install GIT from the software manager, we will need it later
    - Restart now or after you install your preferred IDE

### IDE Example setup - IntelliJ
- Within your VM install JetBrains Toolbox from the jetbrains website https://www.jetbrains.com/toolbox-app/
- Install IntelliJ IDEA Community Edition from the toolbox
    - Note as of Summer '23 - version 2022.1.4 is the latest that supports the python plugins for some reason so install this version.

### Coding and running Environment
Using a local IDE of your choice, add the GIT repos we will need and set up the virtual environment to access helper functions 
 
- (Create a GITHUB account if you have not already - github.com)
- Git clone ssh://git@github.com/rileeki-org/synthetic-database-project to your IDE
- Download and execute synthea: [synthea setup page](https://github.com/synthetichealth/synthea/wiki/Basic-Setup-and-Running)
- Create a virtual environment to access shared helper functions
  - Background reading: [VIRTUAL ENVIRONMENTS 1](https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/), [VIRTUAL ENVIRONMENTS 2](https://openclassrooms.com/en/courses/6900846-set-up-a-python-environment/6990546-manage-virtual-environments-using-requirements-files)
  - Generate SSH keys on your machine and then add your key to your github account
    - [Generating a SSH key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)
    - [Adding your SSH key to github](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)
  - Run: $ sudo apt install python3-pip     (Installs the Python3 version of "pip" on your system, allowing you to easily install and manage Python packages)
  - Run: $ pip install -r [YOUR REPO PATH]/synthetic-database-project/requirements.txt
- Prepare to run synthea
  - if you haven't already, install synthea-with-dependencies.jar: [Download Link](https://github.com/synthetichealth/synthea/releases/download/master-branch-latest/synthea-with-dependencies.jar)
  - move synthea-with-dependencies.jar into your project directory (where run_synthea.py lives)
  - Run: $ python run_synthea.py --If the command 'python' is not found, use 'python3'


    
