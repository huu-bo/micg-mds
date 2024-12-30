# micg-mds
an implementation of moerdescript (unfinished)\
`python3`

![Moerdescript logo](https://snoworange420.github.io/assets/moerdescript.png)

# Setup
Only works on x86-64 Linux, requires python3 and nasm

```shell
nasm runtime.asm -f elf64 -o runtime.o
```

main.py compiles main.mds to a.elf (It also creates temporary files temp.asm and temp.o)
