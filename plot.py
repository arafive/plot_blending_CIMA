
import os
import rasterio

import cartopy.crs as ccrs
import cartopy.feature as cfeature

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.colors import ListedColormap
from matplotlib.colors import BoundaryNorm

plt.rc('font', weight='normal', size=6)

lista_possibili_cartelle_lavoro = [
    '/media/daniele/Daniele2TB/repo/plot_blending_CIMA',
    '/run/media/daniele.carnevale/Daniele2TB/repo/plot_blending_CIMA',
]

cartella_lavoro = [
    x for x in lista_possibili_cartelle_lavoro if os.path.exists(x)][0]
os.chdir(cartella_lavoro)
del (lista_possibili_cartelle_lavoro)


def f_open_tiff(percorso_tif, coordinate):
    with rasterio.open(percorso_tif) as src:
        data      = src.read(1)  # Legge la prima banda
        
        # if os.path.exists(f"{cartella_output_figure}/{str(tempo_UTC).split('+')[0].replace(' ', '_').replace(':', '-')}.png"):
        #     continue
        
        # print(tempo_UTC)
        # plt.imshow(data)
        # plt.title(str(tempo_UTC))
        # plt.savefig(f"{cartella_output_figure}/{str(tempo_UTC).split('+')[0].replace(' ', '_').replace(':', '-')}.png", dpi=300, format='png', bbox_inches='tight')
        # plt.close()
        # continue
    
        data[data == -9999.0] = 0
        
        data_orig = src.read(1)
        data_orig = np.where(data_orig == -9999.0, 0, 1)
        
        transform = src.transform  # Matrice di trasformazione affine
        # crs = src.crs  # Sistema di riferimento delle coordinate
        altezza, larghezza = data.shape  # Prendo le dimensioni
        
        ### Per avere informazioni sui metadati (non mi servono, li commento)
        # meta = src.meta
        # profile = src.profile
        # tags = src.tags()
        
    ### Prendo gli indici di ogni cella
    righe, colonne = np.meshgrid(np.arange(altezza), np.arange(larghezza), indexing='ij')

    ### Converto questi indici in coordinate
    lon, lat = rasterio.transform.xy(transform, righe, colonne, offset='center')
    lon, lat = np.reshape(lon, (altezza, larghezza)), np.reshape(lat, (altezza, larghezza))
    
    ### Estraggo solo quello che riguarda "coordinate"
    mask = (lat >= coordinate[2]) & (lat <= coordinate[3]) & (lon >= coordinate[0]) & (lon <= coordinate[1])

    sub_righe, sub_colonne = np.where(mask)
    sub_righe_min, sub_righe_max = sub_righe.min(), sub_righe.max()
    sub_colonne_min, sub_colonne_max = sub_colonne.min(), sub_colonne.max()
    
    sub_data_2D = data[sub_righe_min:sub_righe_max + 1, sub_colonne_min:sub_colonne_max + 1]
    sub_lat_2D = lat[sub_righe_min:sub_righe_max + 1, sub_colonne_min:sub_colonne_max + 1]
    sub_lon_2D = lon[sub_righe_min:sub_righe_max + 1, sub_colonne_min:sub_colonne_max + 1]
    
    return sub_data_2D, sub_lat_2D, sub_lon_2D


def f_plot(asse, data, lat, lon):
    p = asse.contourf(
        lon,
        lat,
        data,
        levels=livelli,
        cmap=cmap,
        norm=norm,
        extend="both",
        transform=ccrs.PlateCarree()
    )

    asse.contour(
        lon,
        lat,
        data,
        levels=livelli,
        colors='black',
        linewidths=0.1,
        transform=ccrs.PlateCarree()
    )
    
    return p

# %%

coordinate = (7.2, 10.5, 43.1, 45.4)
lista_tempi = pd.date_range('2025-09-01 00:00:00', '2025-09-02 23:30:00', freq='30min')

colori = ["#ffffff", "#e0ebff", "#b5c9ff", "#8eb2ff", "#7f96ff", "#6370f7", "#009f1e", "#3cbc3d", "#b9f96e", "#fff914", "#ffa30a", "#e50000", "#bd0000"]
livelli = [1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

cmap = ListedColormap(colori[1:-1])
cmap.set_under(colori[0])
cmap.set_over(colori[-1])
norm = BoundaryNorm(livelli, cmap.N)

os.makedirs('./plot', exist_ok=True)

cartella_merging_DPC = '/mnt/ARC_STORICO/RADAR/ARCHIVIO_RADAR_DPC/MCM/2025/09'

n = 0
for tempo in lista_tempi:
    print(tempo)
    
    cartella_tif = f"{tempo.day:02d}/{tempo.strftime('%H%M')}"
    
    lista_tif = sorted(os.listdir(cartella_tif))

    dict_cartella = {x: {y: None for y in lista_tif} for x in ['blending', 'mcm1']}
    
    for tif in lista_tif:
        percorso_tif = f'{cartella_tif}/{tif}'
        
        
        data_blend, lat_blend, lon_blend = f_open_tiff(percorso_tif, coordinate)
        try:
            percorso_dpc_tif = f"{cartella_merging_DPC}/01/mcm1_{tif.split('.tif')[0].split('_')[-1]}.tif"
            data_dpc, lat_dpc, lon_dpc = f_open_tiff(percorso_dpc_tif, coordinate)
        except rasterio.RasterioIOError:
            percorso_dpc_tif = f"{cartella_merging_DPC}/02/mcm1_{tif.split('.tif')[0].split('_')[-1]}.tif"
            data_dpc, lat_dpc, lon_dpc = f_open_tiff(percorso_dpc_tif, coordinate)
        
        dict_cartella['blending'][tif] = data_blend
        dict_cartella['mcm1'][tif] = data_dpc
        

    fig, axs = plt.subplots(9, 2, figsize=(8, 12), subplot_kw={'projection': ccrs.PlateCarree()})
    
    fig.suptitle(pd.to_datetime(lista_tif[0].split('_')[1]), y=0.91, fontsize=10, fontweight='bold')

    for ax in axs.flat:
        ax.coastlines(resolution='10m')
        ax.add_feature(cfeature.BORDERS)
        ax.set_extent(coordinate)
        ax.set_aspect('auto', adjustable=None)

    for i, tif in enumerate(lista_tif):
        plot_shade = f_plot(axs[i, 0], dict_cartella['blending'][tif], lat_blend, lon_blend)
        
        percorso_dpc_tif = f"{cartella_merging_DPC}/01/mcm1_{tif.split('.tif')[0].split('_')[-1]}.tif"
            
        plot_shade = f_plot(axs[i, 1], dict_cartella['mcm1'][tif], lat_dpc, lon_dpc)
    
        valid_time = pd.to_datetime(percorso_dpc_tif.split('/')[-1].split('.')[0].split('_')[-1])
        axs[i, 0].set_title(valid_time, loc='left', fontsize=6, y=0.95)

    cbar = fig.colorbar(
        plot_shade,
        ax=axs,
        orientation="horizontal",
        ticks=livelli,
        extend="both",
        drawedges=True,
        shrink=0.85,
        pad=0.025,
        aspect=50
    )
    
    cbar.ax.tick_params(labelsize=10, length=0)

    plt.savefig(f"./plot/{lista_tif[0].split('_')[1]}.png", dpi=300, format='png', bbox_inches='tight')
        
    # plt.show()
    plt.close()
    
    # sss
        
        
print('\n\nDone')
