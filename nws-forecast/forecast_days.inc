#errorCatcher Echo
#encoding UTF-8
<div>
   <table style='width: 100%;border-bottom:1pt solid LightGray;padding:15px;'>
     <tr>
       <th style="text-align:center">Daily</th>
       <th style="text-align:center">Hourly</th>
       </tr>
    <tr style="vertical-align:top">
       <td style='width: 60%;'>
       #set $title_font_size = 'small'
       #set $forecast_generated_at = ''
#for $twelve_hour in $nwsforecast.twelve_hour_forecasts()
       #set $forecast_generated_at = $twelve_hour.generatedTime ##.format('%a %l %p')
       <table style='width:100%;border-right:1pt solid LightGray;padding:15px;'>
          <tr style='width:100%;'>
            <th colspan="2" style='text-align:center;font-size:$title_font_size;font-weight:bold;border-bottom:1pt solid LightGray;'>
              $twelve_hour.name</td>
          </tr>
          <tr>
             <td style='width:20%;'>
                <table style='width:100%;text-align:left;'>
                   <tr style='width:100%;'><td>$twelve_hour.outTemp.format('%.0f') $twelve_hour.outTempTrend </td></tr>
                   <tr style='width:100%;'><td>Wind $twelve_hour.windSpeed $twelve_hour.windDir.ordinal_compass</td></tr>
                </table>
             </td>
             <td style='width:80%;'>
                <table style='width:100%;text-align:left;'>
                   <tr style='width:100%;'><td>$twelve_hour.detailedForecast</td></tr>
                </table>
             </td>
            </tr>
          </table>
#end for
          </td>
    <td style='width: 40%;'>
      #set title_font_size = 'large'
      #set $forecast_generated_at = ''
      #for $hour in $nwsforecast.one_hour_forecasts(12)
      #set $forecast_generated_at = $hour.generatedTime
          <table style='width:100%;border-bottom:none;padding:0px;'>
            <tr>
              <td style='width:20%;'>$hour.startTime.format('%-I %p')</td>
              <td style='width:30%;'>$hour.shortForecast</td>
              <td style='width:20%;'>$hour.outTemp.format('%.0f')</td>
              <td style='width:30%;'>$hour.windSpeed $hour.windDir.ordinal_compass</td>
            </tr>
          </table>
      #end for
      </td>
   </tr>
  </table>
    #if $forecast_generated_at != ''
      <td style='text-align:center;font-style:italic;color:Gray;'>Forecast generated $forecast_generated_at.</td>
    #end if
</div>
