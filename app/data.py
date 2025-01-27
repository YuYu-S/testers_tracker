""" Yield and pack data.

Copyright (C) Seagate Technology LLC, 2025. All rights reserved.
"""
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict

class DataError(Exception): pass

class Data:

    PASS_BIN_DISK_LEN  = 6
    PASS_BIN_DISK_MDWC = 'C000'
    PASS_BIN_HEAD      = 1

    def __init__(self):

        self.n_heads = 48
        self.n_disks = self.n_heads // 2

        self.disks = [f'disk_{disk:2d}' for disk in range(self.n_disks)]
        self.heads = [f'head_{head:2d}' for head in range(self.n_heads)]

        # Define the base set of pack info attributes
        header = [
            'MX', 'pack_num', 'end_date', 'end_time', 'tester', 'rpm', 'profile', 'prod_id',
            'production_version', 'media_from', 'ta_num', 'hsa_num', 'hub_sn', 'pack_aft_reboot',
            'n_head_cal', 'rcc', 'rcc_message', 'disk_sn_out', 'disk_sn_in', 'duration', 'ir'
        ]

        self.pack_header = header + self.disks + self.heads

    def getPacksData(self, path_data: str, n_hours: float) -> pd.DataFrame:
        """
            Get pack information from csv files under ``path_dir`` with provided the number of hours
            and join them together in DataFrame.
        """
        packs = pd.DataFrame()

        files = [fn for fn in os.listdir(path_data) if fn.endswith('csv')]
        for file in files:

            df_csv = pd.read_csv(os.path.join(path_data, file), header=None, delim_whitespace=False)

            filename = file.strip('.csv')

            # Filter only csv file with pack number to avoid getting other csv file in the folder.
            if df_csv.apply(lambda row: filename in row.astype(str).values, axis=1).any():

                packs = pd.concat([packs, df_csv], ignore_index=True)

        if not packs.empty:

            packs.columns = self.pack_header

            # create a new column to combine date and time
            packs['date_time'] = packs['end_date'] + ' ' + packs['end_time']

            # convert ``date_time`` column into datatime type
            packs['date_time'] = pd.to_datetime(packs['date_time'], format='%d-%b-%Y %H:%M')

            filter_date = datetime.now() - timedelta(hours=n_hours)

            packs = packs[(packs['date_time'] >= filter_date)]

        else:
            raise DataError(f'No "csv" file in {path_data}. Closing "Testers Tracker" app.')

        return packs

    def getBinCount(self, bins: pd.DataFrame, include_pass_bin: bool = True) -> pd.DataFrame:
        """ Return the bins with their respective counts."""
        # Flatten bins to 1D array
        bins_1d = bins.to_numpy().ravel()

        bin_count = pd.Series(bins_1d).value_counts().reset_index()

        bin_count.columns = ['bin', 'count']
        # Filter out pass_bin if ``include_pass_bin = False``. The criteria for `pass` bins:
        # Bins that either have length equal to the defined PASS_BIN_DISK_LEN, or start with 'C000'
        # and do not end with digits
        if not include_pass_bin:

            if bin_count['bin'].dtype == object:
                bin_count = bin_count[
                    ~
                    ((bin_count['bin'].str.len() == self.PASS_BIN_DISK_LEN)
                     | (bin_count['bin'].str.startswith(self.PASS_BIN_DISK_MDWC)
                        & ~bin_count['bin'].str[-3:].str.isdigit())
                     )
                ]

            else:
                bin_count = bin_count[~(bin_count['bin'] == self.PASS_BIN_HEAD)]

        return bin_count

    def getDiskBins(self, bins: pd.DataFrame) -> Tuple[int, int, int]:
        """ return the number of passed bins, failed bins and detcr bins."""
        # Melt the bins DataFrame to get a single 'bin' column
        bins = bins.melt(value_name='bin')

        bins_detcr = bins['bin'].str.startswith('D')

        bins_pass  = ((bins['bin'].str.len() == self.PASS_BIN_DISK_LEN) |
                     (bins['bin'].str.startswith(self.PASS_BIN_DISK_MDWC) &
                      ~bins['bin'].str[-3:].str.isdigit()))

        bins_fail = ~(bins_pass | bins_detcr)

        return len(bins[bins_pass]), len(bins[bins_fail]), len(bins[bins_detcr])

    def getRccSummary(self, data: pd.DataFrame) -> pd.DataFrame:

        rcc         = data[data['rcc'] != 0]
        rcc_summary = rcc[['tester', 'date_time', 'rcc', 'rcc_message']]
        rcc_summary = rcc_summary.sort_values('tester').reset_index(drop=True)

        return rcc_summary

    def getYieldSummary(self, packs: pd.DataFrame) -> pd.DataFrame:

        yields = pd.DataFrame(
            columns=['tester', 'type', 'disk_pass', 'disk_fail', 'disks_fail_from_C', 'pack',
                     'yield %']
        )

        testers = packs['tester'].unique()
        for tester in testers:

            tester_packs = packs[packs['tester'] == tester]
            tester_disks = tester_packs[self.disks]

            tester_type = 'mdsw' if 'mdsw' in tester_packs['profile'].iloc[0] else 'mdwc'

            disks_pass, disks_fail, disks_detcr = self.getDiskBins(tester_disks)

            n_packs = int((disks_pass + disks_fail + disks_detcr) / 24)

            # mdsw yield calculation excludes disks_detcr
            tester_yield = round(disks_pass * 100 / (disks_pass + disks_fail), 2)

            yield_summary = pd.DataFrame(
                [[tester, tester_type, disks_pass, disks_fail, disks_detcr, n_packs, tester_yield]],
                columns = yields.columns
            )

            yields = pd.concat([yields, yield_summary])

        yields = yields.sort_values('tester')

        return yields

    def getData(
        self,
        data_path:   str,
        export_path: Optional[str],
        n_hours:     float
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

        packs = self.getPacksData(data_path, n_hours)

        filtered_pack_data = packs[
            ['pack_num', 'MX', 'tester', 'date_time', 'hsa_num', 'hub_sn', 'pack_aft_reboot',
             'n_head_cal', 'rcc', 'rcc_message'] + self.disks + self.heads
        ]

        # Exclude ``data_time`` column before exporting packs information.
        export_packs = packs.drop(columns=['date_time'])

        rcc_summary   = self.getRccSummary(packs)
        yield_summary = self.getYieldSummary(packs)

        head_bins = self.getBinCount(packs[self.heads], include_pass_bin=False)
        disk_bins = self.getBinCount(packs[self.disks], include_pass_bin=False)

        export_data = {
            'data'           : export_packs,
            'yield'          : yield_summary,
            'rcc_summary'    : rcc_summary,
            'head_bins_count': head_bins,
            'disk_bins_count': disk_bins,
        }

        if export_path:
            self.exportData(export_data, export_path)

        # fileter yield summary for yield table

        yield_data = yield_summary[['tester', 'type', 'yield %']].copy()

        yield_data['tester'] = yield_data['tester'].apply(lambda t: f'T{t}')

        yield_data.set_index('tester', inplace=True)

        return filtered_pack_data, yield_data, rcc_summary

    def exportData(self, dfs_sheets: Dict[str, pd.DataFrame], fn_dir: str):

        filename = f'output_{datetime.now().strftime("%d%m%y_%H%M%S")}'

        with pd.ExcelWriter(os.path.join(fn_dir, f'{filename}.xlsx')) as writer:
            for sheet, df in dfs_sheets.items():
                df.to_excel(writer, sheet_name=sheet, index=False)
