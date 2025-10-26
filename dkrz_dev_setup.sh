# Prepare your system
#sudo apt-get update && apt-get upgrade

# Install packages required by spack
#sudo apt-get update
#sudo apt-get install bzip2 ca-certificates g++ gcc gfortran git gzip lsb-release patch python3 tar unzip xz-utils zstd

compiler=gcc@13

# Install spack and add to local shell
git clone --depth=2 https://github.com/spack/spack.git 

export SPACK_ROOT=$PWD/spack
echo $SPACK_ROOT
. $SPACK_ROOT/share/spack/setup-env.sh

spack compiler find
spack install --fresh $compiler

# Activate creation of module files via spack
spack config add "modules:default:enable:[tcl]"

# change this for you compiler of choice, has to be done for compatibility with levant.dkrz.de
#spack compiler add "$(spack location -i $compiler%$compiler)"
spack compiler find
spack compilers

# Install and setup "module" and add to local shell
spack install lmod %$compiler
. $(spack location -i lmod)/lmod/lmod/init/profile
. $SPACK_ROOT/share/spack/setup-env.sh
spack install git %$compiler
spack install nano %$compiler

python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt


# Add to end of home/user/.bashrc via nano or similar from within your home/user directory
#. ~/spack/share/spack/setup-env.sh
#. $SPACK_ROOT/share/spack/setup-env.sh
#. $(spack location -i lmod)/lmod/lmod/init/profile

# All other packages can be explicitly request by providing a dictionary filled with potential spack envs
# which will then be install and managed for you.