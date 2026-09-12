clear; close all; clc;

num = 10.^(4:0.2:7);
alpha = 2 ./ sqrt(num);

gt = ((1 + cos(alpha)) / 2).^(num-2);
single_res = ((1 + cos(single(alpha))) / 2).^(num-2);
exp_res = exp(-single(alpha).^2/4.*(num-2));

figure(1); clf;
set(gcf, 'position', [450, 300, [600, 450] * 1.2]);

hold on;
plot(num, single_res - gt, 'o', 'markersize', 8, 'linewidth', 2);
plot(num, exp_res - gt, '^', 'markersize', 8, 'linewidth', 2);
plot(num, zeros(size(num)), 'k:', 'linewidth', 1.2);
box on;

set(gca, 'xscale', 'log', 'fontsize', 13);
legend({'$$\big(\frac{1}{2}(1 + \cos\alpha)\big)^N$$', '$$\exp\big(-\frac{1}{4}\alpha^2 N\big)$$'}, 'fontsize', 13, ...
    'interpreter', 'latex');
xlabel('Number of points', 'fontsize', 16);
ylabel('Error', 'fontsize', 16);
title('Numerical error of different methods', 'fontsize', 18);

% saveas(gcf, 'img/numerical_err.png');