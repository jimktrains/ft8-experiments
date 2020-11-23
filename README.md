# ft8-experiments

Some experiments on decoding FT8. They're going to specifically be
focused on ways I might be able to decode them on my
[mcHF](http://www.m0nka.co.uk/?page_id=2) running
[UHSDR](https://github.com/df8oe/UHSDR) with an STM32 F4 having either
256kB or 512Kb of RAM, which cannot store 15sec of samples and as such
would require some form of streaming decoding. This means that I will
not be able to decode all transmissions, especially those whose initial
sync sequences are missing and most likely those which cannot be decoded
via a naive demodulator with the help of the LDPC decoder.

(Yes, I know this isn't the method laid out in papers, such as those in
the repo, on how FT8 is normally decoded. I'm willing to sacrifice
sensitivity of the decoder to enable decoding at all. I do think that I
can apply some of what is normally done to aid in decoding, but the
constraints of the hardware make any backtracking or multiple passes
difficult.)

Next step is to take the output and turn it into bytes and run through
the LDPC to get error correction.

Once I think the decoder works, is to build something that
will process the whole band sequentially.

Beyond that I'd like to go back and see about teasing out weaker
signals.

Some Samples output currently.  

![558Hz SNR=3](558Hz_SNR_3.png)
![1045Hz SNR=-4](1045Hz_SNR_-7.png)
![690Hz SNR=-22](690Hz_SNR_-22.png)
