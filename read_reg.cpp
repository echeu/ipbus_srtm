// Short program to read from /dev/mem
// Compile: g++ -o read_reg read_reg.cpp
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
   // u32 *bram32_vptr
   int fd;

   if (argc < 2) std::cout << "Usage: read_reg <address>. Do not use preface number with 0x, just use beeffeed format" << std::endl;
   else {

     // Convert input argument to hex address
     std::stringstream str;
     str << argv[1];
     str >> std::hex >> bram_pbase;
     //     bram_pbase = std::stoi(argv[1], 0, 16);
     //std::cout << "address: " << std::hex << bram_pbase << std::endl;
     base_addr = (bram_pbase/4096) * 4096;
     //std::cout << "base address: " << std::hex << base_addr << std::endl;

     if (bram_pbase > 0 && (fd = open("/dev/mem", O_RDWR | O_SYNC)) != -1) {
	 
	 // Map the BRAM physical address into user space getting a virtual address for it
	 bram32_vptr = (int *)mmap(NULL, bram_size, PROT_READ|PROT_WRITE, MAP_SHARED, fd, base_addr);

	 int offset = (bram_pbase%4096)/4;
	 //std::cout << "offset: " << offset << std::endl;
	 int num = bram32_vptr[offset];
	 std::cout << "0x" <<  std::hex << num ;
	 //std::cout <<  num ;

	 //	 for (int i=0; i<32; i++) {
	 //	   std::cout << "offset: " << i << std::hex << bram32_vptr[i] << std::endl;
	 //	 }
	 close(fd);

	return num;
     }
   }
}

