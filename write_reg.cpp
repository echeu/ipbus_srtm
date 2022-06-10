// Short program to write to /dev/mem
// Compile: g++ -o write_reg.exe write_reg.cpp
// Use version in /opt/pkg/petalinux/2018.3/tools/linux-i386/aarch64-linux-gnu/bin

#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <stdio.h>
#include <iostream>
#include <sstream>

//typedef long int u32;

int main(int argc, char** argv) {
   unsigned int bram_size = 0x8000;
   off_t bram_pbase = 0x80001000; // physical base address
   off_t base_addr;
   int *bram32_vptr;
   off_t number;
   // u32 *bram32_vptr
   int fd;

   if (argc < 3) std::cout << "Usage: write_reg <address> <value>. Do not use preface number with 0x, just use beeffeed format" << std::endl;
   else {

     // Convert input arguments to hex address
     std::stringstream str, str2;
     str << argv[1];
     str >> std::hex >> bram_pbase;

     std::cout << "argv[2]: " << argv[2] << std::endl;
     str2 << argv[2];
     str2 >> std::hex >> number;
     std::cout << "Number: " << std::hex << number << std::endl;

     std::cout << "address: " << std::hex << bram_pbase << std::endl;
     base_addr = (bram_pbase/4096) * 4096;
     std::cout << "base address: " << std::hex << base_addr << std::endl;

     if (bram_pbase > 0 && (fd = open("/dev/mem", O_RDWR | O_SYNC)) != -1) {
	 
	 // Map the BRAM physical address into user space getting a virtual address for it
	 bram32_vptr = (int *)mmap(NULL, bram_size, PROT_READ|PROT_WRITE, MAP_SHARED, fd, base_addr);

	 int offset = (bram_pbase%4096)/4;
	 std::cout << "offset: " << offset;
	 std::cout << "writing value: " << number << std::endl;
	 bram32_vptr[offset] = number;
	 close(fd);
     }
   }
}

