# Prepare your system
#sudo apt-get update && apt-get upgrade

# Install packages required by spack
#sudo apt-get update
#sudo apt-get install bzip2 ca-certificates g++ gcc gfortran git gzip lsb-release patch python3 tar unzip xz-utils zstd

# Install spack and add to local shell
git clone --depth=2 https://github.com/spack/spack.git --branch v1.1.1

export HPFF_SPACK_ROOT=$PWD/spack
. spack/share/spack/setup-env.sh
. $HPFF_SPACK_ROOT/share/spack/setup-env.sh

spack compiler find

# Activate creation of module files via spack
spack config add "modules:default:enable:[tcl]"

# change this for you compiler of choice, has to be done for compatibility with levant.dkrz.de
#spack compiler add "$(spack location -i $compiler%$compiler)"

spack compilers

# Install and setup "module" and add to local shell
#spack install --fresh lmod
#. $(spack location -i lmod)/lmod/lmod/init/profile
#. $HPFF_SPACK_ROOT/share/spack/setup-env.sh

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt


# Add to end of home/user/.bashrc via nano or similar from within your home/user directory
#. ~/spack/share/spack/setup-env.sh
#. $SPACK_ROOT/share/spack/setup-env.sh
#. $(spack location -i lmod)/lmod/lmod/init/profile

# All other packages can be explicitly request by providing a dictionary filled with potential spack env
# which will then be install and managed for you.