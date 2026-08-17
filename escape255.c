#include <stdio.h>
#include <unistd.h>

int main(void) {
    unsigned char ch;
    while (read(STDIN_FILENO, &ch, 1) > 0) {
        if (ch == 0xFF) {
            unsigned char dbg[2] = {0xFF, 0xFF};
            write(STDOUT_FILENO, dbg, 2);
        } else {
            write(STDOUT_FILENO, &ch, 1);
        }
    }
    return 0;
}
