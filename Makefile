################################################################################
# Makefile for reading i2c values.
################################################################################
# ECC - try compiling with aarch64 compiler instead of default compiler

# compiler
CC = /opt/pkg/petalinux/2018.3/tools/linux-i386/aarch64-linux-gnu/bin/aarch64-linux-gnu-g++



# All Target
all: read_reg write_reg

# Tool invocations
read_reg:	
	@echo 'Building target: $@.exe'
	$(CC)  $@.cpp  -o $@.exe
	@echo 'Finished building target: $@'
	@echo ' '

write_reg:	
	@echo 'Building target: $@.exe'
	$(CC)  $@.cpp  -o $@.exe
	@echo 'Finished building target: $@.exe'
	@echo ' '


# Other Targets

.PHONY: all dependents
.SECONDARY:

