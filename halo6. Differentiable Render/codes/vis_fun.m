function y = vis_fun(x, black_lim, white_lim)
y = (x + black_lim) * white_lim ./ (x + white_lim);
y = log10(y);

y = (y - log10(black_lim)) / (log10(white_lim) - log10(black_lim));
end