#!/usr/bin/env perl
my @src_lines;
while (<>) {
    chomp;
    push(@src_lines, $_);
}
my @lines = @src_lines;
my ($start_addr) = map { hex $_ } ((shift @lines) =~ /^\s*\.BEGIN\s+(\d+)\s*$/);
(pop @lines) =~ /^\s*.END\s*$/ || die 'no valid .END';
my %symbols;
for ($i = 0; $i < scalar @lines; ++$i) {
    if ($lines[$i] =~ /^([A-Z0-9]+):\s+(.+)$/) {
        $symbols{$1} = $start_addr + 2 * $i;
        $lines[$i] = $2;
    }
    $lines[$i] = [$start_addr + 2 * $i, $lines[$i], $src_lines[$i + 1]];
}
my %mnem2code = (
    HLT => 0x0, READ => 0x1, WRITE => 0x2, LD => 0x3, ST => 0x4, TAD => 0x5, CLEAR => 0x6, CIR => 0x7,
    SUB => 0x8, DEC => 0x9, INC => 0xA, CMP => 0xB, JMP => 0xC, JMPGT => 0xD, JMPLT => 0xE, JMPEQ => 0xF
);
printf("LOCATION    OBJECT CODE    SOURCE\n");
printf("%12s%15s%s\n", "", "", $src_lines[0]);
foreach (@lines) {
    my ($loc, $line, $src_line) = @$_;
    my ($mnem, $args_str) = ($line =~ /^\s*([A-Z.]+)\s*(.*)$/);
    my $code = 0x0;
    if ($mnem eq ".DATA") {
        $code |= (unpack('S', pack('s', int($args_str))))[0];
    } else {
        $code |= $mnem2code{$mnem} << 12;
        foreach (split /,\s*/, $args_str) {
            if ($_ eq "R1") { $code |= 0b01 << 10; }
            elsif ($_ eq "R2") { $code |= 0b10 << 10; }
            else { $code |= $symbols{$_} || hex($_); }
        }
        $code |= 0b11 << 10 unless (($code >> 10) & 0b11);
    }
    printf("%03X%9s%04X%11s%s\n", $loc, "", $code, "", $src_line);
}
printf("%12s%15s%s\n", "", "", pop @src_lines);
printf("SYMBOL      LOC\n");
printf("%-12s%03X\n", $_, $symbols{$_}) foreach (sort keys %symbols);
