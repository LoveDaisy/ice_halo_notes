clear; close all; clc;

data_folder = '../data';
load(sprintf('%s/column1.0_rp35_180+15.mat', data_folder));

bin_file = fopen(sprintf('%s/data_251x801.bin', data_folder), 'r');
bin_data = fread(bin_file, [251, 801], 'float=>double')';

dr = 7;
w = 99;
k = 2^(-dr);

white_lim = prctile(halo_img.img(:), w);
black_lim = k * white_lim;

figure(1); clf;
subplot(1,2,1);

imagesc(halo_img.img_x, -halo_img.img_y, ...
    srgb_inverse_gamma(vis_fun(halo_img.img, black_lim, white_lim)));
axis equal; axis tight; axis xy;
colormap gray;

subplot(1,2,2);

imagesc(halo_img.img_x, -halo_img.img_y, ...
    srgb_inverse_gamma(vis_fun(bin_data, black_lim, white_lim)));
axis equal; axis tight; axis xy;
colormap gray;